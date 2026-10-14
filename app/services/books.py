from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.author import Author
from app.models.category import Category
from app.schemas.book import BookCreate, BookUpdate


async def _load_book(db: AsyncSession, book_id: int) -> Book:
    result = await db.execute(
        select(Book)
        .options(selectinload(Book.author), selectinload(Book.category))
        .where(Book.id == book_id)
    )
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado.")
    return book


async def list_books(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    category_id: int | None = None,
    author_id: int | None = None,
) -> list[Book]:
    query = (
        select(Book)
        .options(selectinload(Book.author), selectinload(Book.category))
        .offset(skip)
        .limit(limit)
    )
    if category_id:
        query = query.where(Book.category_id == category_id)
    if author_id:
        query = query.where(Book.author_id == author_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_book(db: AsyncSession, book_id: int) -> Book:
    return await _load_book(db, book_id)


async def create_book(db: AsyncSession, data: BookCreate) -> Book:
    # Validate FK existence
    author = await db.get(Author, data.author_id)
    if not author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor não encontrado.")
    category = await db.get(Category, data.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada."
        )

    # Check ISBN uniqueness
    existing = await db.execute(select(Book).where(Book.isbn == data.isbn))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="ISBN já cadastrado."
        )

    book = Book(**data.model_dump())
    db.add(book)
    await db.commit()
    return await _load_book(db, book.id)


async def update_book(db: AsyncSession, book_id: int, data: BookUpdate) -> Book:
    book = await _load_book(db, book_id)
    update_data = data.model_dump(exclude_unset=True)

    if "author_id" in update_data:
        if not await db.get(Author, update_data["author_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Autor não encontrado."
            )
    if "category_id" in update_data:
        if not await db.get(Category, update_data["category_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada."
            )
    if "isbn" in update_data and update_data["isbn"] != book.isbn:
        existing = await db.execute(
            select(Book).where(Book.isbn == update_data["isbn"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="ISBN já cadastrado."
            )

    for field, value in update_data.items():
        setattr(book, field, value)

    await db.commit()
    return await _load_book(db, book_id)


async def delete_book(db: AsyncSession, book_id: int) -> None:
    book = await _load_book(db, book_id)
    await db.delete(book)
    await db.commit()
