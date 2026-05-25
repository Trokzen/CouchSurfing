"""
Integration tests for Authentication API.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, db_session):
    """Test successful user registration."""
    payload = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "full_name": "New User",
        "role": "guest"
    }
    
    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert "id" in data
    assert "password" not in data

    # Verify in DB
    result = await db_session.execute(select(User).where(User.email == payload["email"]))
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == "New User"

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, guest_user):
    """Test registration with an already existing email."""
    payload = {
        "email": guest_user.email,
        "password": "anotherpassword",
        "full_name": "Duplicate User",
        "role": "guest"
    }
    
    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, guest_user):
    """Test successful login."""
    login_data = {
        "username": guest_user.email,
        "password": "password123"
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, guest_user):
    """Test login with wrong password."""
    login_data = {
        "username": guest_user.email,
        "password": "wrongpassword"
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers, guest_user):
    """Test getting current user profile."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == guest_user.email
    assert data["id"] == guest_user.id
