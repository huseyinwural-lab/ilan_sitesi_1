
import pytest
from httpx import AsyncClient, ASGITransport
from server import app
from app.dependencies import get_current_user
from unittest.mock import MagicMock
import uuid

@pytest.mark.asyncio
async def test_admin_masterdata_rbac():
    # 1. Mock Country Admin
    country_admin = MagicMock()
    country_admin.id = uuid.uuid4()
    country_admin.role = "country_admin"
    country_admin.email = "ca@platform.com"
    
    app.dependency_overrides[get_current_user] = lambda: country_admin
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # List Attributes (Allowed)
        res = await client.get("/api/v1/admin/master-data/attributes")
        assert res.status_code == 200
        
        # Try Config Update (Forbidden)
        # Need a valid ID, assume one from list or mock
        attr_id = str(uuid.uuid4()) # Won't exist but check permission first
        # Ideally we fetch one from list if seed ran, but let's assume 404 is better than 403 if allowed.
        # But we expect 403 before 404 check if decorator is robust, OR logic check inside.
        # Our logic: Fetch -> Check -> 403. So we need valid ID.
        # Let's rely on list
        if len(res.json()) > 0:
            attr_id = res.json()[0]["id"]
            
            res_patch = await client.patch(f"/api/v1/admin/master-data/attributes/{attr_id}", json={
                "is_active": False
            })
            assert res_patch.status_code == 403
            
            # Try Label Update (Allowed)
            res_patch_label = await client.patch(f"/api/v1/admin/master-data/attributes/{attr_id}", json={
                "name": {"en": "New Name"}
            })
            assert res_patch_label.status_code == 200

    # 2. Mock Super Admin
    super_admin = MagicMock()
    super_admin.id = uuid.uuid4()
    super_admin.role = "super_admin"
    super_admin.email = "sa@platform.com"
    
    app.dependency_overrides[get_current_user] = lambda: super_admin
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Config Update (Allowed)
        if len(res.json()) > 0:
            attr_id = res.json()[0]["id"]
            res_patch = await client.patch(f"/api/v1/admin/master-data/attributes/{attr_id}", json={
                "is_active": True
            })
            assert res_patch.status_code == 200
