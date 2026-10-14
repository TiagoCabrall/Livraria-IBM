import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.deps import get_db
from app.main import app
import app.models  # noqa: F401 — registers all ORM models with Base.metadata

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(DATABASE_URL, echo=False)
AsyncTestSessionLocal = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with AsyncTestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with AsyncTestSessionLocal() as session:
        yield session


# Helper factories

async def create_user(client: AsyncClient, email: str = "user@test.com", password: str = "Secret1", full_name: str = "Test User"):
    resp = await client.post("/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name,
    })
    assert resp.status_code == 201
    return resp.json()


async def login(client: AsyncClient, email: str = "user@test.com", password: str = "Secret1") -> str:
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def create_category(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/categories/",
        json={"name": "Fiction", "slug": "fiction", "description": "Fiction books"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()


async def create_author(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/authors/",
        json={"name": "Jane Doe", "bio": "A great author"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()


async def create_book(client: AsyncClient, token: str, category_id: int, author_id: int) -> dict:
    resp = await client.post(
        "/books/",
        json={
            "title": "Test Book",
            "isbn": "978-3-16-148410-0",
            "description": "A great read",
            "price": "29.90",
            "stock": 10,
            "author_id": author_id,
            "category_id": category_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()


async def make_admin(db_session, email: str):
    from sqlalchemy import select, update
    from app.models.user import User, UserRole
    await db_session.execute(
        update(User).where(User.email == email).values(role=UserRole.admin)
    )
    await db_session.commit()
