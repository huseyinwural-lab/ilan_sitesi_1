
import pytest
from httpx import AsyncClient, ASGITransport
from server import app

@pytest.mark.asyncio
async def test_error_standard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. 404 Not Found
        res = await client.get("/api/unknown-endpoint")
        assert res.status_code == 404
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "not_found"
        assert "request_id" in data["error"]
        
        # 2. 422 Validation
        # Send bad JSON to an endpoint expecting body
        res = await client.post("/api/auth/login", json={"email": "bad-email"})
        assert res.status_code == 422
        data = res.json()
        assert data["error"]["code"] == "validation_error"
        assert "details" in data["error"]
