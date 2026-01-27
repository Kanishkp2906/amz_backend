from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from datetime import datetime
from decimal import Decimal

class ProductBase(BaseModel):
    title: str = Field(..., min_length=3, description='Title of the product')
    amazon_url: HttpUrl = Field(..., description='Shortened Amazon URL of the product')
    current_price: Decimal = Field(..., description='Current price of the product', decimal_places=2)
    
class ProductCreate(BaseModel):
    url: HttpUrl

class ProductResponse(ProductBase):
    id: int = Field(..., description='ID of the product')
    last_checked: datetime = Field(..., description='Last date the product was checked')

    model_config = ConfigDict(from_attributes=True)