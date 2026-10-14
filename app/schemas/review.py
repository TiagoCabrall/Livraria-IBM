from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    book_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    book_id: int
    user_id: int
    rating: int
    comment: str | None
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
