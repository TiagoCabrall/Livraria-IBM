from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemOut, CartItemUpdate, CartOut
from app.services import cart as cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartOut)
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.get_cart(db, current_user.id)


@router.post("/items", response_model=CartItemOut, status_code=201)
async def add_item(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.add_to_cart(db, current_user.id, data.book_id, data.quantity)


@router.put("/items/{item_id}", response_model=CartItemOut)
async def update_item(
    item_id: int,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await cart_service.update_cart_item(db, current_user.id, item_id, data.quantity)


@router.delete("/items/{item_id}", status_code=204)
async def remove_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await cart_service.remove_from_cart(db, current_user.id, item_id)


@router.delete("/", status_code=204)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await cart_service.clear_cart(db, current_user.id)
