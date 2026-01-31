from amz_script import get_amazon_price
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import joinedload
from fastapi import APIRouter, HTTPException, Depends, status, Cookie, Response, Query
from database import get_db
from utils.current_time import get_current_time
import uuid
import asyncio
from config import CRON_SECRET
from typing import List
from utils.url_shortener import url_shortner
from models import *
from schemas.users import *
from schemas.products import *
from schemas.price_history import *
from schemas.tracking import *
from utils.email_alert import check_and_send_alerts
import os

is_production = os.getenv("RENDER") is not None

router = APIRouter()

# Verify the domain is actaully an amazon domain.
def verify_amazon_domain(product: ProductCreate) -> ProductCreate:
    domain = product.url.host

    if not domain or "amazon" not in domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Domain - Only Amazon URLs are allowed."
        )
    return product

# Route to start tracking a product from user.
@router.post("/track_product", response_model=TrackingResponse)
async def track_product(
    response: Response,
    data: ProductCreate,
    db: Session = Depends(get_db),
    user_session: str | None = Cookie(default=None)
    ):

    data = verify_amazon_domain(data)
    # Getting the url from the user and checking if the product already exists.
    product_url = str(data.url)
    clean_url = url_shortner(product_url)

    existing_product = db.query(Products).filter(Products.amazon_url == clean_url).first()

    if existing_product:
        print(f"Product already exists: {existing_product.title}")
        product_id = existing_product.id
        product_current_price = existing_product.current_price
    
    else:
        product_data = await get_amazon_price(product_url)
        title = product_data['title']
        current_price = product_data['price']
        image_url = product_data['image_url']

        if title is None and current_price == 0.0 and image_url is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to fetch product details. Please try again later."
            )

        new_product = Products(
            title = title,
            current_price = current_price,
            amazon_url = clean_url,
            image_url = image_url
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        product_id = new_product.id
        product_current_price = new_product.current_price

    # Check if the user is new or already tracking a product.
    if user_session is None:
        user_uuid = str(uuid.uuid4())
        new_user = Users(user_uuid = user_uuid, is_active = True)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user_id = new_user.id

        response.set_cookie(
            key="user_session",
            value=user_uuid,
            httponly=True,
            secure=is_production,
            samesite=None if is_production else None,
            max_age=31536000,
            path="/",
            domain=None
            )

    else:
        user = db.query(Users).filter(Users.user_uuid == user_session).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')
        user_id = user.id

    # Check if this specific user is *already* tracking this specific product.
    existing_tracking = db.query(Tracking).filter(
        Tracking.user_id == user_id,
        Tracking.product_id == product_id
        ).first()
    
    if existing_tracking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='You are already tracking this product.'
        )

    new_tracking = Tracking(
        user_id = user_id,
        product_id = product_id,
        initial_price = product_current_price,
        last_alert_price = None
    )
    db.add(new_tracking)
    db.commit()
    db.refresh(new_tracking)

    return new_tracking

# Route to return current user's all tracking products.
@router.get('/tracking_products', response_model=List[TrackingResponse])
async def all_tracking_products(db: Session = Depends(get_db), user_session: str | None = Cookie(default=None)):
    if not user_session:
        return []
    
    user = db.query(Users).options(
        joinedload(Users.tracking).joinedload(Tracking.product)
        ).filter(Users.user_uuid == user_session).first()

    return user.tracking

# Route to return the product details of a selected product.
@router.get('/product_details/{product_id}', response_model=ProductResponse)
async def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    user_session: str | None = Cookie(default=None)
    ):

    if not user_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')
    
    user = db.query(Users).filter(Users.user_uuid == user_session).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')
    
    tracking_entry = db.query(Tracking).filter(
        Tracking.user_id == user.id, Tracking.product_id == product_id
    ).first()

    if not tracking_entry:
        raise HTTPException(status_code=404, detail="Product not found in your tracking list")
    
    product = db.query(Products).filter(Products.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail='Product not found.')
    
    return product

@router.delete("/delete_tracking/{product_id}", response_model=ProductResponse)
async def delete_product_tracking(
    product_id: int,
    db: Session = Depends(get_db),
    user_session: str | None = Cookie(default=None)
    ):

    if not user_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = db.query(Users).filter(Users.user_uuid == user_session).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    tracking = db.query(Tracking).filter(Tracking.user_id == user.id, Tracking.product_id == product_id).first()
    if not tracking:
        raise HTTPException(status_code=404, detail="You are not tracking this product.")
    
    product = db.query(Products).filter(Products.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    db.delete(tracking)
    db.flush()
    
    remaining_tracking = db.query(Tracking).filter(Tracking.product_id == product_id).first()
    
    if not remaining_tracking:
        response_data = ProductResponse.model_validate(product)
        db.delete(product)
        db.commit()
        return response_data
    else:
        db.commit()
        return product

# Making a semaphore limit to run the tasks with limit and to not load up the server.
semaphore = asyncio.Semaphore(3)

# Method to update the price and last_checked of the product and create price_history.
async def update_single_product(product_id: int, url: str, db: Session):
    current_datetime = get_current_time()
    async with semaphore:
        try:
            print(f"Starting update for: {product_id}...")
            data = await get_amazon_price(url)
            new_price = data['price']

            product = db.query(Products).filter(Products.id == product_id).first()

            if product:
                product.current_price = new_price
                product.last_checked = current_datetime

                history_entry = PriceHistory(
                    product_id = product_id,
                    price = new_price,
                    recorded_at = current_datetime
                )
                db.add(history_entry)
                db.commit()
                print(f"Updated Product {product_id} to {new_price}")
                return True
            
        except Exception as e:
            print(f"Failed to update product {product_id}: {e}")
            return False

# Route for the cron-job to hit and run the tasks to update the price of the products.     
@router.get('/cron/update_prices')
async def daily_price_update(token: str = Query(...), db: Session = Depends(get_db)):
    if token != CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid Token'
        )
    
    products = db.query(Products).all()
    if not products:
        return {'message': 'No products to update.'}
    
    print(f"Starting bulk update for {len(products)} products...")

    tasks = []
    for product in products:
        task = update_single_product(product.id, product.amazon_url, db)
        tasks.append(task)

    result = await asyncio.gather(*tasks)

    success_count = result.count(True)
    fail_count = result.count(False)

    check_and_send_alerts(db)

    return {
        'status': 'Completed',
        'total products': len(products),
        'successful updates': success_count,
        'failed_updates': fail_count
    }    

# Route to submit the user's email.
@router.put("/submit_email", response_model=UserResponse)
async def submit_user_email(request: EmailRequest, db: Session = Depends(get_db), user_session: str | None = Cookie(default=None)):
    if not user_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not Authorized.')
    
    user = db.query(Users).filter(Users.user_uuid == user_session).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    existing_email = db.query(Users).filter(Users.email == request.email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists. Use a different email.")
    
    if user.email == request.email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='You are already using this email.')
    
    user.email = request.email
    db.commit()
    db.refresh(user)

    return user
