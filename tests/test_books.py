import pytest
from httpx import AsyncClient

from tests.conftest import create_author, create_book, create_category, create_user, login, make_admin

pytestmark = pytest.mark.asyncio


async def _setup_admin(client, db_session):
    await create_user(client, email="admin@test.com")
    await make_admin(db_session, "admin@test.com")
    token = await login(client, email="admin@test.com")
    cat = await create_category(client, token)
    author = await create_author(client, token)
    return token, cat, author


async def test_list_books_empty(client: AsyncClient):
    resp = await client.get("/books/")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_book(client: AsyncClient, db_session):
    token, cat, author = await _setup_admin(client, db_session)
    book = await create_book(client, token, cat["id"], author["id"])
    assert book["title"] == "Test Book"
    assert book["author"]["name"] == "Jane Doe"
    assert book["category"]["name"] == "Fiction"


async def test_create_book_non_admin(client: AsyncClient, db_session):
    await create_user(client)
    token = await login(client)
    # Need category and author created by admin first
    await create_user(client, email="admin@test.com")
    await make_admin(db_session, "admin@test.com")
    admin_token = await login(client, email="admin@test.com")
    cat = await create_category(client, admin_token)
    author = await create_author(client, admin_token)

    resp = await client.post(
        "/books/",
        json={
            "title": "Bad Book",
            "isbn": "978-0-00-000000-1",
            "price": "10.00",
            "stock": 5,
            "author_id": author["id"],
            "category_id": cat["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_get_book(client: AsyncClient, db_session):
    token, cat, author = await _setup_admin(client, db_session)
    book = await create_book(client, token, cat["id"], author["id"])
    resp = await client.get(f"/books/{book['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == book["id"]


async def test_get_book_not_found(client: AsyncClient):
    resp = await client.get("/books/9999")
    assert resp.status_code == 404


async def test_update_book(client: AsyncClient, db_session):
    token, cat, author = await _setup_admin(client, db_session)
    book = await create_book(client, token, cat["id"], author["id"])
    resp = await client.put(
        f"/books/{book['id']}",
        json={"price": "49.90", "stock": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == "49.90"


async def test_delete_book(client: AsyncClient, db_session):
    token, cat, author = await _setup_admin(client, db_session)
    book = await create_book(client, token, cat["id"], author["id"])
    resp = await client.delete(
        f"/books/{book['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    # Confirm gone
    resp = await client.get(f"/books/{book['id']}")
    assert resp.status_code == 404


async def test_list_books_filter_by_category(client: AsyncClient, db_session):
    token, cat, author = await _setup_admin(client, db_session)
    await create_book(client, token, cat["id"], author["id"])
    resp = await client.get(f"/books/?category_id={cat['id']}")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_duplicate_isbn(client: AsyncClient, db_session):
    token, cat, author = await _setup_admin(client, db_session)
    await create_book(client, token, cat["id"], author["id"])
    resp = await client.post(
        "/books/",
        json={
            "title": "Another Book",
            "isbn": "978-3-16-148410-0",  # same ISBN
            "price": "19.90",
            "stock": 3,
            "author_id": author["id"],
            "category_id": cat["id"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409
