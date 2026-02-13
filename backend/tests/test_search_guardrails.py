
import pytest
from httpx import AsyncClient, ASGITransport
from server import app
from unittest.mock import patch, MagicMock
from app.dependencies import get_current_user
import json

@pytest.mark.asyncio
async def test_search_guardrails():
    # We need to mock get_current_user to None (anonymous) or bypass it
    # Search is public, no auth dependency usually.
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Page Size Limit
        res = await client.get("/api/v2/search?limit=101")
        assert res.status_code == 422
        data = res.json()
        assert data["error"]["code"] == "validation_error"
        # The detail message might come from Pydantic or custom logic.
        # Our Pydantic validation handles Query(le=100) or we enforce manually.
        # Let's see implementation.
        
        # 2. Max Filters
        filters = {f"f{i}": i for i in range(11)}
        res = await client.get(f"/api/v2/search?attrs={json.dumps(filters)}")
        assert res.status_code == 422
        assert data["error"]["code"] == "validation_error" or data["error"]["code"] == "query_too_complex"

@pytest.mark.asyncio
async def test_search_rate_limit():
    # Mock Redis Limit check to return False
    # RateLimiter is used as dependency.
    # We need to override the dependency or mock the RedisRateLimiter inside the route.
    
    # Since we instantiate `RedisRateLimiter` in `search_routes.py` (we will add it),
    # we need to mock THAT instance.
    
    # Let's simulate Rate Limit Exceeded by mocking check_limit
    mock_limiter = MagicMock()
    async def mock_check(*args, **kwargs):
        return False # Blocked
    mock_limiter.check_limit = mock_check
    
    # We need to patch where it is used.
    # It will be used in `app/routers/search_routes.py`
    with patch("app.routers.search_routes.search_limiter.check_limit", new=mock_check):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/v2/search")
            assert res.status_code == 429
            data = res.json()
            assert data["error"]["code"] == "rate_limit_exceeded"
