from pydantic import BaseModel, ConfigDict
from datetime import datetime
from schemas.products import ProductResponse

class TrackingCreate(BaseModel):
    product_id: int

class TrackingResponse(BaseModel):
    id: int
    product_id: int
    user_id: int
    created_at: datetime
    product: ProductResponse

    model_config = ConfigDict(from_attributes=True)