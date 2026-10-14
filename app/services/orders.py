from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.book import Book
from app.models.cart import CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.services.cart import clear_cart


async def _load_order(db: AsyncSession, order_id: int, user_id: int | None = None) -> Order:
    query = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.author),
            selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.category),
        )
        .where(Order.id == order_id)
    )
    if user_id is not None:
        query = query.where(Order.user_id == user_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado."
        )
    return order


async def create_order(db: AsyncSession, user_id: int, shipping_address: str) -> Order:
    result = await db.execute(
        select(CartItem)
        .options(selectinload(CartItem.book))
        .where(CartItem.user_id == user_id)
    )
    cart_items = list(result.scalars().all())
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Carrinho está vazio."
        )

    total = Decimal("0.00")
    order_items: list[OrderItem] = []

    for cart_item in cart_items:
        book = await db.get(Book, cart_item.book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Livro id={cart_item.book_id} não encontrado.",
            )
        if book.stock < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Estoque insuficiente para '{book.title}'.",
            )
        book.stock -= cart_item.quantity
        unit_price = Decimal(str(book.price))
        total += unit_price * cart_item.quantity
        order_items.append(
            OrderItem(book_id=book.id, quantity=cart_item.quantity, unit_price=unit_price)
        )

    order = Order(
        user_id=user_id,
        shipping_address=shipping_address,
        total_amount=total,
        status=OrderStatus.pending,
    )
    db.add(order)
    await db.flush()  # get order.id before adding items

    for item in order_items:
        item.order_id = order.id
        db.add(item)

    await clear_cart(db, user_id)
    await db.commit()
    return await _load_order(db, order.id, user_id)


async def list_orders(db: AsyncSession, user_id: int) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.author),
            selectinload(Order.items).selectinload(OrderItem.book).selectinload(Book.category),
        )
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: int, user_id: int) -> Order:
    return await _load_order(db, order_id, user_id)


async def cancel_order(db: AsyncSession, order_id: int, user_id: int) -> Order:
    order = await _load_order(db, order_id, user_id)
    if order.status not in (OrderStatus.pending, OrderStatus.confirmed):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Pedido com status '{order.status}' não pode ser cancelado.",
        )
    # Restore stock
    for item in order.items:
        book = await db.get(Book, item.book_id)
        if book:
            book.stock += item.quantity

    order.status = OrderStatus.cancelled
    await db.commit()
    return await _load_order(db, order_id, user_id)
