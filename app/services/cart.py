from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import CartItem
from app.models.book import Book
from app.schemas.cart import CartOut


async def _load_cart_item(db: AsyncSession, item_id: int, user_id: int) -> CartItem:
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.book).selectinload(Book.author),
                 selectinload(CartItem.book).selectinload(Book.category))
        .where(CartItem.id == item_id, CartItem.user_id == user_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item do carrinho não encontrado."
        )
    return item


async def get_cart(db: AsyncSession, user_id: int) -> CartOut:
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.book).selectinload(Book.author),
                 selectinload(CartItem.book).selectinload(Book.category))
        .where(CartItem.user_id == user_id)
    )
    items = list(result.scalars().all())
    total = sum(Decimal(str(item.book.price)) * item.quantity for item in items)
    return CartOut(items=items, total=total)


async def add_to_cart(db: AsyncSession, user_id: int, book_id: int, quantity: int) -> CartItem:
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Livro não encontrado.")
    if book.stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estoque insuficiente. Disponível: {book.stock}.",
        )

    result = await db.execute(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.book_id == book_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        new_qty = existing.quantity + quantity
        if book.stock < new_qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Estoque insuficiente. Disponível: {book.stock}.",
            )
        existing.quantity = new_qty
        await db.commit()
        return await _load_cart_item(db, existing.id, user_id)

    item = CartItem(user_id=user_id, book_id=book_id, quantity=quantity)
    db.add(item)
    await db.commit()
    return await _load_cart_item(db, item.id, user_id)


async def update_cart_item(
    db: AsyncSession, user_id: int, item_id: int, quantity: int
) -> CartItem:
    item = await _load_cart_item(db, item_id, user_id)
    book = await db.get(Book, item.book_id)
    if book and book.stock < quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estoque insuficiente. Disponível: {book.stock}.",
        )
    item.quantity = quantity
    await db.commit()
    return await _load_cart_item(db, item_id, user_id)


async def remove_from_cart(db: AsyncSession, user_id: int, item_id: int) -> None:
    item = await _load_cart_item(db, item_id, user_id)
    await db.delete(item)
    await db.commit()


async def clear_cart(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(select(CartItem).where(CartItem.user_id == user_id))
    for item in result.scalars().all():
        await db.delete(item)
    await db.commit()
