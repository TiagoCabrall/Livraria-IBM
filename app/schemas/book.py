from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.author import AuthorOut
from app.schemas.category import CategoryOut


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    isbn: str = Field(min_length=10, max_length=17)
    description: str | None = None
    price: Decimal = Field(gt=Decimal("0"), decimal_places=2)
    stock: int = Field(ge=0)
    cover_url: str | None = Field(default=None, max_length=500)
    author_id: int
    category_id: int


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=10, max_length=17)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=Decimal("0"), decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    cover_url: str | None = Field(default=None, max_length=500)
    author_id: int | None = None
    category_id: int | None = None


class BookOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    isbn: str
    description: str | None
    price: Decimal
    stock: int
    cover_url: str | None
    author: AuthorOut
    category: CategoryOut
