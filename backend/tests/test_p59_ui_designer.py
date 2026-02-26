"""
P59 UI Designer Foundation Tests
- ADMIN_UI_DESIGNER permission check
- UI Config API (header) contract: create draft, publish, effective resolve
- Scope resolution: system config fallback and tenant config override
- Theme CRUD + assignment + effective resolve
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


def get_auth_token(email: str, password: str, portal: str = "admin") -> str:
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"X-Portal-Scope": portal}
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed for {email}: {response.status_code} - {response.text[:200]}")
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for tests"""
    return get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer token for tests"""
    return get_auth_token(DEALER_EMAIL, DEALER_PASSWORD, "dealer")


class TestUIDesignerPermissions:
    """Test ADMIN_UI_DESIGNER permission enforcement"""
    
    def test_permissions_endpoint_super_admin_200(self, admin_token):
        """Super admin should get 200 on /api/admin/ui/permissions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/permissions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200 for super_admin, got {response.status_code}"
        data = response.json()
        assert data.get("permission") == "ADMIN_UI_DESIGNER"
        assert "super_admin" in data.get("roles", [])
        assert "country_admin" in data.get("roles", [])
        assert data.get("enabled") is True
        print(f"✓ Permissions endpoint returned: {data}")
    
    def test_permissions_endpoint_dealer_403(self, dealer_token):
        """Dealer (yetkisiz rol) should get 403 on /api/admin/ui/permissions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/permissions",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"
        print(f"✓ Dealer correctly denied with 403")

    def test_admin_ui_configs_endpoint_dealer_403(self, dealer_token):
        """Dealer should get 403 on /api/admin/ui/configs/header"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for dealer on configs, got {response.status_code}"
        print(f"✓ Dealer correctly denied configs endpoint with 403")

    def test_admin_ui_themes_endpoint_dealer_403(self, dealer_token):
        """Dealer should get 403 on /api/admin/ui/themes"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/themes",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for dealer on themes, got {response.status_code}"
        print(f"✓ Dealer correctly denied themes endpoint with 403")


class TestUIConfigAPI:
    """Test UI Config (header) API contract"""
    
    def test_get_header_config_draft(self, admin_token):
        """GET /api/admin/ui/configs/header returns draft config structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header?segment=individual&scope=system&status=draft",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Got {response.status_code}: {response.text[:200]}"
        data = response.json()
        # item can be None if no drafts exist yet
        assert "item" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✓ Header draft config response: item={'present' if data['item'] else 'null'}, items_count={len(data['items'])}")
    
    def test_create_header_config_draft(self, admin_token):
        """POST /api/admin/ui/configs/header creates a draft config"""
        test_config_data = {
            "logo_url": "/assets/test-logo.png",
            "nav_items": [
                {"label": "Test Nav 1", "href": "/test1"},
                {"label": "Test Nav 2", "href": "/test2"}
            ],
            "test_timestamp": str(int(time.time()))
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "system",
                "scope_id": None,
                "status": "draft",
                "config_data": test_config_data
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200, f"Got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert data.get("ok") is True
        assert "item" in data
        item = data["item"]
        assert item.get("config_type") == "header"
        assert item.get("segment") == "individual"
        assert item.get("scope") == "system"
        assert item.get("status") == "draft"
        assert "id" in item
        assert "version" in item
        assert item.get("config_data") == test_config_data
        print(f"✓ Created draft config: id={item['id']}, version={item['version']}")
        return item
    
    def test_create_and_publish_header_config(self, admin_token):
        """POST draft + POST publish creates a published config"""
        # Step 1: Create draft
        test_config_data = {
            "logo_url": "/assets/publish-test-logo.png",
            "publish_test": str(uuid.uuid4())
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "system",
                "scope_id": None,
                "status": "draft",
                "config_data": test_config_data
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert draft_response.status_code == 200, f"Draft creation failed: {draft_response.text[:200]}"
        draft_data = draft_response.json()
        config_id = draft_data["item"]["id"]
        
        # Step 2: Publish
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/publish/{config_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert publish_response.status_code == 200, f"Publish failed: {publish_response.text[:200]}"
        publish_data = publish_response.json()
        assert publish_data.get("ok") is True
        item = publish_data["item"]
        assert item.get("status") == "published"
        assert item.get("published_at") is not None
        print(f"✓ Published config: id={item['id']}, version={item['version']}, published_at={item['published_at']}")
        return item
    
    def test_effective_config_endpoint(self, admin_token):
        """GET /api/ui/header returns effective config (public endpoint)"""
        response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=individual",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "config_type" in data
        assert data["config_type"] == "header"
        assert "segment" in data
        assert "source_scope" in data
        assert "config_data" in data
        print(f"✓ Effective header config: source_scope={data['source_scope']}, source_scope_id={data.get('source_scope_id')}")


class TestScopeResolution:
    """Test scope resolution: system fallback and tenant override"""
    
    def test_tenant_scope_override(self, admin_token):
        """Tenant config should override system config"""
        tenant_id = "test-tenant-001"
        unique_marker = str(uuid.uuid4())
        
        # Step 1: Create system-level published config
        system_config = {
            "level": "system",
            "marker": f"system-{unique_marker}"
        }
        
        requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "corporate",
                "scope": "system",
                "scope_id": None,
                "status": "published",
                "config_data": system_config
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        
        # Step 2: Create tenant-level published config
        tenant_config = {
            "level": "tenant",
            "tenant_id": tenant_id,
            "marker": f"tenant-{unique_marker}"
        }
        
        tenant_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": tenant_id,
                "status": "published",
                "config_data": tenant_config
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert tenant_response.status_code == 200, f"Tenant config creation failed: {tenant_response.text[:200]}"
        
        # Step 3: Verify effective config with tenant_id resolves to tenant config
        effective_response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=corporate&tenant_id={tenant_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert effective_response.status_code == 200
        effective_data = effective_response.json()
        
        assert effective_data.get("source_scope") == "tenant", f"Expected source_scope=tenant, got {effective_data.get('source_scope')}"
        assert effective_data.get("source_scope_id") == tenant_id
        assert effective_data.get("config_data", {}).get("level") == "tenant"
        print(f"✓ Tenant override works: source_scope={effective_data['source_scope']}, marker={effective_data.get('config_data', {}).get('marker')}")
    
    def test_system_fallback_when_no_tenant_config(self, admin_token):
        """System config should be used as fallback when no tenant config exists"""
        nonexistent_tenant = f"nonexistent-{uuid.uuid4()}"
        
        # Request effective config for a tenant that doesn't have its own config
        response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=individual&tenant_id={nonexistent_tenant}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should fall back to system or return default
        assert data.get("source_scope") in ["system", "default"]
        print(f"✓ System fallback works: source_scope={data['source_scope']}")


class TestThemeCRUD:
    """Test Theme CRUD operations"""
    
    def test_list_themes(self, admin_token):
        """GET /api/admin/ui/themes returns theme list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/themes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✓ Theme list: {len(data['items'])} themes")
    
    def test_create_theme(self, admin_token):
        """POST /api/admin/ui/themes creates a new theme"""
        theme_name = f"Test Theme {uuid.uuid4().hex[:8]}"
        tokens = {
            "primary": "#3b82f6",
            "secondary": "#10b981",
            "accent": "#f97316",
            "background": "#ffffff",
            "text": "#111827"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={
                "name": theme_name,
                "tokens": tokens,
                "is_active": False
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200, f"Got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert data.get("ok") is True
        item = data["item"]
        assert item.get("name") == theme_name
        assert item.get("tokens") == tokens
        assert item.get("is_active") is False
        assert "id" in item
        print(f"✓ Created theme: id={item['id']}, name={item['name']}")
        return item
    
    def test_get_single_theme(self, admin_token):
        """GET /api/admin/ui/themes/{theme_id} returns theme detail"""
        # First create a theme
        theme_name = f"Detail Test Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {"test": "value"}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Get the theme
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/themes/{theme_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["item"]["id"] == theme_id
        assert data["item"]["name"] == theme_name
        print(f"✓ Got theme detail: {theme_name}")
    
    def test_update_theme(self, admin_token):
        """PATCH /api/admin/ui/themes/{theme_id} updates theme"""
        # Create theme
        theme_name = f"Update Test Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {"original": "value"}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Update theme
        new_name = f"Updated {theme_name}"
        new_tokens = {"updated": "new_value", "added": "field"}
        response = requests.patch(
            f"{BASE_URL}/api/admin/ui/themes/{theme_id}",
            json={"name": new_name, "tokens": new_tokens},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data["item"]["name"] == new_name
        assert data["item"]["tokens"] == new_tokens
        print(f"✓ Updated theme: {new_name}")
    
    def test_activate_theme(self, admin_token):
        """PATCH /api/admin/ui/themes/{theme_id} with is_active=true"""
        # Create theme
        theme_name = f"Activate Test Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Activate
        response = requests.patch(
            f"{BASE_URL}/api/admin/ui/themes/{theme_id}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        assert response.json()["item"]["is_active"] is True
        print(f"✓ Activated theme: {theme_name}")
    
    def test_delete_theme(self, admin_token):
        """DELETE /api/admin/ui/themes/{theme_id} deletes theme"""
        # Create theme
        theme_name = f"Delete Test Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Delete
        response = requests.delete(
            f"{BASE_URL}/api/admin/ui/themes/{theme_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json().get("ok") is True
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/admin/ui/themes/{theme_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404
        print(f"✓ Deleted theme: {theme_name}")


class TestThemeAssignment:
    """Test Theme assignment and effective resolve"""
    
    def test_list_theme_assignments(self, admin_token):
        """GET /api/admin/ui/theme-assignments returns assignment list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ Theme assignments: {len(data['items'])} assignments")
    
    def test_assign_theme_to_system(self, admin_token):
        """POST /api/admin/ui/theme-assignments assigns theme to system scope"""
        # Create theme
        theme_name = f"System Assignment Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {"system_test": "value"}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Assign to system
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={
                "theme_id": theme_id,
                "scope": "system",
                "scope_id": None
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data["item"]["scope"] == "system"
        assert data["item"]["theme_id"] == theme_id
        print(f"✓ Assigned theme to system scope")
    
    def test_assign_theme_to_tenant(self, admin_token):
        """POST /api/admin/ui/theme-assignments assigns theme to tenant scope"""
        tenant_id = f"tenant-{uuid.uuid4().hex[:8]}"
        
        # Create theme
        theme_name = f"Tenant Assignment Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {"tenant_test": tenant_id}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Assign to tenant
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={
                "theme_id": theme_id,
                "scope": "tenant",
                "scope_id": tenant_id
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data["item"]["scope"] == "tenant"
        assert data["item"]["scope_id"] == tenant_id
        print(f"✓ Assigned theme to tenant: {tenant_id}")
    
    def test_effective_theme_resolve(self, admin_token):
        """GET /api/ui/themes/effective returns effective theme"""
        response = requests.get(
            f"{BASE_URL}/api/ui/themes/effective",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "source_scope" in data
        assert "tokens" in data
        print(f"✓ Effective theme: source_scope={data['source_scope']}, theme={data.get('theme', {}).get('name')}")
    
    def test_effective_theme_tenant_override(self, admin_token):
        """Tenant theme assignment should override system"""
        tenant_id = f"theme-tenant-{uuid.uuid4().hex[:8]}"
        
        # Create unique theme for tenant
        theme_name = f"Tenant Override Theme {uuid.uuid4().hex[:8]}"
        theme_tokens = {"override_marker": tenant_id}
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": theme_tokens, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        # Assign to tenant
        requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={"theme_id": theme_id, "scope": "tenant", "scope_id": tenant_id},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        
        # Get effective theme for this tenant
        response = requests.get(
            f"{BASE_URL}/api/ui/themes/effective?tenant_id={tenant_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["source_scope"] == "tenant"
        assert data["source_scope_id"] == tenant_id
        assert data["tokens"].get("override_marker") == tenant_id
        print(f"✓ Tenant theme override works: tokens={data['tokens']}")
    
    def test_delete_theme_assignment(self, admin_token):
        """DELETE /api/admin/ui/theme-assignments/{assignment_id}"""
        tenant_id = f"delete-assign-{uuid.uuid4().hex[:8]}"
        
        # Create theme and assign
        theme_name = f"Delete Assignment Theme {uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": theme_name, "tokens": {}, "is_active": False},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        theme_id = create_response.json()["item"]["id"]
        
        assign_response = requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={"theme_id": theme_id, "scope": "tenant", "scope_id": tenant_id},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assignment_id = assign_response.json()["item"]["id"]
        
        # Delete assignment
        response = requests.delete(
            f"{BASE_URL}/api/admin/ui/theme-assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json().get("ok") is True
        print(f"✓ Deleted theme assignment")


class TestValidation:
    """Test validation and error handling"""
    
    def test_invalid_segment_returns_400(self, admin_token):
        """Invalid segment should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header?segment=invalid_segment",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print(f"✓ Invalid segment correctly returns 400")
    
    def test_invalid_scope_returns_400(self, admin_token):
        """Invalid scope should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header?scope=invalid_scope",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print(f"✓ Invalid scope correctly returns 400")
    
    def test_tenant_scope_requires_scope_id(self, admin_token):
        """Tenant scope without scope_id should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": None,  # Missing scope_id
                "status": "draft",
                "config_data": {}
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400
        print(f"✓ Tenant scope without scope_id correctly returns 400")
    
    def test_invalid_config_type_returns_400(self, admin_token):
        """Invalid config_type should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/invalid_type",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print(f"✓ Invalid config_type correctly returns 400")
    
    def test_invalid_theme_id_returns_400(self, admin_token):
        """Invalid theme_id format should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/themes/not-a-uuid",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        print(f"✓ Invalid theme_id format correctly returns 400")
    
    def test_nonexistent_theme_returns_404(self, admin_token):
        """Non-existent theme should return 404"""
        fake_uuid = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/themes/{fake_uuid}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print(f"✓ Non-existent theme correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
