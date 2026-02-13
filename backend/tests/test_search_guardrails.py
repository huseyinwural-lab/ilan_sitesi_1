
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
    
    # We need to mock redis check_limit because Rate Limiter is enforced now
    # By default we want it to PASS for guardrail tests (except the RL test)
    mock_limiter_pass = MagicMock()
    async def mock_check_pass(*args, **kwargs):
        return True
    mock_limiter_pass.check_limit = mock_check_pass
    
    with patch("app.routers.search_routes.search_limiter.check_limit", new=mock_check_pass):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Page Size Limit
            res = await client.get("/api/v2/search?limit=101")
            assert res.status_code == 422
            data = res.json()
            # Validation error structure
            assert data["error"]["code"] == "validation_error"
            
            # 2. Max Filters
            filters = {f"f{i}": i for i in range(11)}
            res = await client.get(f"/api/v2/search?attrs={json.dumps(filters)}")
            assert res.status_code == 422
            data = res.json()
            assert data["error"]["code"] == "query_too_complex"

@pytest.mark.asyncio
async def test_search_rate_limit():
    # Simulate Rate Limit Exceeded
    mock_limiter_fail = MagicMock()
    async def mock_check_fail(*args, **kwargs):
        return False # Blocked
    mock_limiter_fail.check_limit = mock_check_fail
    
    with patch("app.routers.search_routes.search_limiter.check_limit", new=mock_check_fail):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.get("/api/v2/search")
            assert res.status_code == 429
            data = res.json()
            assert data["error"]["code"] == "rate_limit_exceeded"
