"""
Shared fixtures for all tests.
"""
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models import User, Listing, Booking, Review, Message
from app.core.security import get_password_hash
from app.schemas.auth import UserRole, VerificationStatus

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"

_test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Create all tables once per test session."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database):
    """Provide a fresh database session with rollback after each test."""
    async with TestSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Async HTTP client for testing API endpoints."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# ==================== Test data fixtures ====================


@pytest_asyncio.fixture
async def guest_user(db_session: AsyncSession) -> User:
    """Create a test guest user."""
    user = User(
        email="guest@test.com",
        password_hash=get_password_hash("password123"),
        full_name="Test Guest",
        role=UserRole.GUEST,
        verification_status=VerificationStatus.UNVERIFIED,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def host_user(db_session: AsyncSession) -> User:
    """Create a test host user."""
    user = User(
        email="host@test.com",
        password_hash=get_password_hash("password123"),
        full_name="Test Host",
        role=UserRole.HOST,
        verification_status=VerificationStatus.VERIFIED,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def guest_token(client: AsyncClient, guest_user: User) -> str:
    """Get access token for guest user."""
    resp = await client.post("/api/v1/auth/login", data={
        "username": "guest@test.com",
        "password": "password123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def host_token(client: AsyncClient, host_user: User) -> str:
    """Get access token for host user."""
    resp = await client.post("/api/v1/auth/login", data={
        "username": "host@test.com",
        "password": "password123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(guest_token: str) -> dict:
    """Authorization headers for guest."""
    return {"Authorization": f"Bearer {guest_token}"}


@pytest_asyncio.fixture
async def host_headers(host_token: str) -> dict:
    """Authorization headers for host."""
    return {"Authorization": f"Bearer {host_token}"}