from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.book import BookOut


class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=5, max_length=500)


class OrderItemOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    book: BookOut
    quantity: int
    unit_price: Decimal


class OrderOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    status: str
    total_amount: Decimal
    shipping_address: str
    created_at: datetime
    items: list[OrderItemOut]
