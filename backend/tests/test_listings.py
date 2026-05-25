"""
Integration tests for Listings API.
"""
import pytest
from httpx import AsyncClient
from app.models import Listing

@pytest.mark.asyncio
async def test_create_listing_success(client: AsyncClient, host_headers, host_user):
    """Test successful listing creation by a host."""
    payload = {
        "title": "Cozy Apartment in Center",
        "description": "A very nice place to stay with good amenities.",
        "city": "Moscow",
        "address": "Red Square, 1",
        "capacity": 2,
        "amenities": ["wifi", "kitchen"],
        "is_active": True
    }
    
    response = await client.post("/api/v1/listings/", json=payload, headers=host_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["host_id"] == host_user.id

@pytest.mark.asyncio
async def test_create_listing_forbidden_for_guest(client: AsyncClient, auth_headers):
    """Test that a guest cannot create a listing."""
    payload = {
        "title": "Guest's House",
        "description": "Should fail because guest cannot create listings",
        "city": "Moscow",
        "address": "Some address here",
        "capacity": 1,
        "amenities": []
    }
    
    response = await client.post("/api/v1/listings/", json=payload, headers=auth_headers)
    
    # Based on ListingService, it should raise AuthorizationException (403)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_search_listings(client: AsyncClient):
    """Test searching/listing listings."""
    response = await client.get("/api/v1/listings/search")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
