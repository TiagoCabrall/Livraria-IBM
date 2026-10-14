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
    return user_token, book


async def test_empty_cart(client: AsyncClient, db_session):
    await create_user(client)
    token = await login(client)
    resp = await client.get("/cart/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["total"] == "0"


async def test_add_item_to_cart(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    resp = await client.post(
        "/cart/items",
        json={"book_id": book["id"], "quantity": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["quantity"] == 2


async def test_add_item_insufficient_stock(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    resp = await client.post(
        "/cart/items",
        json={"book_id": book["id"], "quantity": 999},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_update_cart_item(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    add_resp = await client.post(
        "/cart/items",
        json={"book_id": book["id"], "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = add_resp.json()["id"]
    resp = await client.put(
        f"/cart/items/{item_id}",
        json={"quantity": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 3


async def test_remove_cart_item(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    add_resp = await client.post(
        "/cart/items",
        json={"book_id": book["id"], "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    item_id = add_resp.json()["id"]
    resp = await client.delete(
        f"/cart/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    cart_resp = await client.get("/cart/", headers={"Authorization": f"Bearer {token}"})
    assert cart_resp.json()["items"] == []


async def test_clear_cart(client: AsyncClient, db_session):
    token, book = await _setup(client, db_session)
    await client.post(
        "/cart/items",
        json={"book_id": book["id"], "quantity": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.delete("/cart/", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204
    cart_resp = await client.get("/cart/", headers={"Authorization": f"Bearer {token}"})
    assert cart_resp.json()["items"] == []


async def test_cart_unauthenticated(client: AsyncClient):
    resp = await client.get("/cart/")
    assert resp.status_code == 403
