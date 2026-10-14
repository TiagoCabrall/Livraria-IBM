from pydantic import BaseModel, Field


class AuthorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    bio: str | None = None
    photo_url: str | None = Field(default=None, max_length=500)


class AuthorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    bio: str | None = None
    photo_url: str | None = Field(default=None, max_length=500)


class AuthorOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    bio: str | None
    photo_url: str | None
