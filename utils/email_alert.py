from sqlalchemy.orm.session import Session
from models import Tracking
from utils.send_email import send_email
from database import Sessionlocal

def check_and_send_alerts(db: Session):
    print("Checking for progressive price drops...")

    trackings = db.query(Tracking).all()

    for tracking in trackings:
        product = tracking.product
        user = tracking.user

        if not tracking.initial_price or not product.current_price:
            continue

        diff = tracking.initial_price - product.current_price
        drop_percentage = (diff / tracking.initial_price) * 100

        if drop_percentage > 10:

            should_notify = False
            if tracking.last_alert_price is None:
                should_notify = True
            elif product.current_price < tracking.last_alert_price:
                should_notify = True

            if should_notify:
                if user.email:
                    print(f"Triggering alert for {user.email} on {product.title[:30]}. Price Drop by {drop_percentage:.2f}%.")

                    subject = f"Price Drop Alert: {product.title[:30]}"

                    body = f"""
                    <html>
                      <body>
                        <h2>Price Drop Alert!</h2>
                        <div style="margin: 20px 0;">
                            <a href="{product.amazon_url}">
                            <img src="{product.image_url}" alt="Product Image" style="max-width: 300px; display: block;">
                            </a>
                        </div>
                        <p>The price of a product you are tracking has dropped by <b>{drop_percentage:.2f}%</b>.</p>
                        <p>Product: <b>{product.title}</b></p>
                        <p>Current Price: <b>₹{product.current_price}</b></p>
                        <p>Initial Price: ₹{tracking.initial_price}</p>
                        <br>
                        <a href="{product.amazon_url}">Buy Now on Amazon</a>
                      </body>
                    </html>
                    """
                    try:
                        send_email(user.email, subject, body)
                        tracking.last_alert_price = product.current_price
                        db.commit()
                    except Exception as e:
                        print(f"Failed to email user {user.id}: {e}")

    print('Alert check complete.')

# if __name__ == "__main__":
#     db = Sessionlocal()
#     try:
#         check_and_send_alerts(db)
#     finally:
#         db.close()

