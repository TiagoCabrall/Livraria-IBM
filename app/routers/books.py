from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, require_admin
from app.schemas.book import BookCreate, BookOut, BookUpdate
from app.services import books as book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=list[BookOut])
async def list_books(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    category_id: int | None = Query(default=None),
    author_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.list_books(db, skip, limit, category_id, author_id)


@router.get("/{book_id}", response_model=BookOut)
async def get_book(book_id: int, db: AsyncSession = Depends(get_db)):
    return await book_service.get_book(db, book_id)


@router.post("/", response_model=BookOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_book(data: BookCreate, db: AsyncSession = Depends(get_db)):
    return await book_service.create_book(db, data)


@router.put("/{book_id}", response_model=BookOut, dependencies=[Depends(require_admin)])
async def update_book(book_id: int, data: BookUpdate, db: AsyncSession = Depends(get_db)):
    return await book_service.update_book(db, book_id, data)


@router.delete("/{book_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    await book_service.delete_book(db, book_id)
