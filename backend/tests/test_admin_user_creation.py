
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from server import app
from app.dependencies import get_current_user
import uuid

@pytest.mark.asyncio
async def test_admin_create_user_flow():
    # Admin User Mock
    admin_user = MagicMock()
    admin_user.id = uuid.uuid4()
    admin_user.role = "super_admin"
    admin_user.email = "admin@platform.com"
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    # Mock Redis (avoid connection error during module load if any)
    mock_redis = MagicMock()
    
    with patch("app.routers.admin_routes.redis_limiter.redis", mock_redis):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Success Case
            res = await client.post("/api/v1/admin/users", json={
                "email": "new.mod@platform.com",
                "password": "Password123!",
                "full_name": "New Mod",
                "role": "moderator",
                "country_scope": ["TR"]
            })
            assert res.status_code == 201
            data = res.json()
            assert data["email"] == "new.mod@platform.com"
            assert data["role"] == "moderator"
            
            # 2. Duplicate Email Case
            res_dupe = await client.post("/api/v1/admin/users", json={
                "email": "new.mod@platform.com",
                "password": "Password123!",
                "full_name": "Dupe",
                "role": "moderator"
            })
            assert res_dupe.status_code == 400
            assert "already exists" in res_dupe.json()["detail"]
            
            # 3. Invalid Role Case
            res_role = await client.post("/api/v1/admin/users", json={
                "email": "bad.role@platform.com",
                "password": "Password123!",
                "full_name": "Bad Role",
                "role": "hacker"
            })
            assert res_role.status_code == 400
            assert "Invalid role" in res_role.json()["detail"]
