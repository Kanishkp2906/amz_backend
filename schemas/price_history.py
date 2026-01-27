from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal

class PriceHistoryBase(BaseModel):
    price: Decimal = Field(..., description='Current price of the product')
    recorded_at: datetime = Field(..., description='Recorded time of the price')

class PriceHistoryCreate(PriceHistoryBase):
    product_id: int

class PriceHistoryResponse(PriceHistoryBase):
    id: int = Field(..., description='ID of the price history')
    product_id: int
    
    model_config = ConfigDict(from_attributes=True)