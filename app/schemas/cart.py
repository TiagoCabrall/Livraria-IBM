from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.book import BookOut


class CartItemAdd(BaseModel):
    book_id: int
    quantity: int = Field(ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartItemOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    book: BookOut
    quantity: int


class CartOut(BaseModel):
    items: list[CartItemOut]
    total: Decimal
