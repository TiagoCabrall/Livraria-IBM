import pytest
from httpx import AsyncClient

from tests.conftest import create_author, create_book, create_category, create_user, login, make_admin

pytestmark = pytest.mark.asyncio


async def _setup(client, db_session):
    await create_user(client, email="admin@test.com")
    await make_admin(db_session, "admin@test.com")
    admin_token = await login(client, email="admin@test.com")
    cat = await create_category(client, admin_token)
    author = await create_author(client, admin_token)
    book = await create_book(client, admin_token, cat["id"], author["id"])

    await create_user(client)
    user_token = await login(client)

    # Add item to cart
    await client.post(
        "/cart/items",
        json={"book_id": book["id"], "quantity": 2},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    return user_token, book


async def test_create_order(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    resp = await client.post(
        "/orders/",
        json={"shipping_address": "Rua das Flores, 123, São Paulo, SP"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


async def test_create_order_empty_cart(client: AsyncClient, db_session):
    await create_user(client)
    token = await login(client)
    resp = await client.post(
        "/orders/",
        json={"shipping_address": "Rua das Flores, 123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


async def test_list_orders(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    await client.post(
        "/orders/",
        json={"shipping_address": "Av Brasil, 456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.get("/orders/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_get_order_detail(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    order_resp = await client.post(
        "/orders/",
        json={"shipping_address": "Rua Test, 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = order_resp.json()["id"]
    resp = await client.get(f"/orders/{order_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == order_id


async def test_cancel_order(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    order_resp = await client.post(
        "/orders/",
        json={"shipping_address": "Rua Cancel, 7"},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = order_resp.json()["id"]
    resp = await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_cancel_already_cancelled_order(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    order_resp = await client.post(
        "/orders/",
        json={"shipping_address": "Rua Test, 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = order_resp.json()["id"]
    await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    # Try to cancel again
    resp = await client.post(
        f"/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_order_not_found(client: AsyncClient, db_session):
    await create_user(client)
    token = await login(client)
    resp = await client.get("/orders/9999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
