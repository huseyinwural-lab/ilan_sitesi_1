
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
import os
import time
from app.core.rate_limit import _rate_limit_store
from server import app
from app.dependencies import get_current_user
import uuid

@pytest.fixture
def clean_rate_limit_store():
    _rate_limit_store.clear()
    yield
    _rate_limit_store.clear()

async def mock_get_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "admin@platform.com"
    user.role = "super_admin"
    return user

@pytest.fixture
def client_with_user():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.mark.asyncio
async def test_rate_limit_ip_based(clean_rate_limit_store):
    # Auth Login is limited to 20/60s (IP Based)
    # We will mock the limiter limit to 2 for faster test
    
    # Since we can't easily change the decorator instance at runtime without reloading,
    # we will rely on the configured limit.
    # The limit is 20.
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Hit 20 times
        for _ in range(20):
            res = await client.post("/api/auth/login", json={"email": "a@b.com", "password": "p"})
            # We expect 401 or 400 (invalid creds) but NOT 429
            assert res.status_code != 429
            
        # 21st time -> 429
        res = await client.post("/api/auth/login", json={"email": "a@b.com", "password": "p"})
        assert res.status_code == 429
        data = res.json()
        # FastAPI wraps exception detail in "detail" key
        error_info = data["detail"]
        assert error_info["code"] == "rate_limit_exceeded"
        assert "Retry-After" in res.headers

@pytest.mark.asyncio
async def test_rate_limit_token_based(clean_rate_limit_store, client_with_user):
    # Listing Create is limited to 60/60s (Authenticated)
    # Mocking higher load is slow.
    # We can patch the Limit value in the instance?
    
    from app.routers.commercial_routes import limiter_listing_create
    original_limit = limiter_listing_create.limit
    limiter_listing_create.limit = 2 # Set low limit
    
    try:
        async with client_with_user as client:
            dealer_id = str(uuid.uuid4())
            # We assume Dealer Validation might fail (404), but Rate Limit runs BEFORE body/logic?
            # Dependencies run first.
            # So even if 404, we count it?
            # Actually, Depends(limiter) runs before the path function.
            # So 404 is returned by the function.
            
            # Hit 1
            res = await client.post(f"/api/v1/commercial/dealers/{dealer_id}/listings", json={"title":"t"}, headers={"Authorization": "Bearer token1"})
            # Expected 404 or 422 (validation) but passed RL
            assert res.status_code != 429
            
            # Hit 2
            res = await client.post(f"/api/v1/commercial/dealers/{dealer_id}/listings", json={"title":"t"}, headers={"Authorization": "Bearer token1"})
            assert res.status_code != 429
            
            # Hit 3 -> Block
            res = await client.post(f"/api/v1/commercial/dealers/{dealer_id}/listings", json={"title":"t"}, headers={"Authorization": "Bearer token1"})
            assert res.status_code == 429
            
            # Different Token -> Pass
            res = await client.post(f"/api/v1/commercial/dealers/{dealer_id}/listings", json={"title":"t"}, headers={"Authorization": "Bearer token2"})
            assert res.status_code != 429
            
    finally:
        limiter_listing_create.limit = original_limit
