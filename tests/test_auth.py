import pytest
from httpx import AsyncClient

from tests.conftest import create_user, login

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "newuser@test.com",
        "password": "Secret1",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "customer"
    assert "hashed_password" not in data


async def test_register_duplicate_email(client: AsyncClient):
    await create_user(client)
    resp = await client.post("/auth/register", json={
        "email": "user@test.com",
        "password": "Secret1",
        "full_name": "Another User",
    })
    assert resp.status_code == 409


async def test_register_weak_password(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "weak@test.com",
        "password": "allower",
        "full_name": "Weak",
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    await create_user(client)
    resp = await client.post("/auth/login", json={
        "email": "user@test.com",
        "password": "Secret1",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await create_user(client)
    resp = await client.post("/auth/login", json={
        "email": "user@test.com",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


async def test_me_authenticated(client: AsyncClient):
    await create_user(client)
    token = await login(client)
    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


async def test_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 403


async def test_update_profile(client: AsyncClient):
    await create_user(client)
    token = await login(client)
    resp = await client.patch(
        "/auth/me",
        json={"full_name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"
