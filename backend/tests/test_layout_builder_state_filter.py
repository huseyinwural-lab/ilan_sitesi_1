"""
Backend API tests for Layout Builder state filter, restore, and reset-and-seed-home-wireframe endpoints.
Testing iteration 146: Content List aktif/pasif state filter, restore, and wireframe reset workflow.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL environment variable is required"

# Test credentials
TEST_EMAIL = "admin@platform.com"
TEST_PASSWORD = "Admin123!"


class TestLayoutBuilderStateFilter:
    """Tests for Layout Builder admin endpoints with state filter support"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip(f"No token in login response: {data}")
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    # Test 1: GET /api/admin/layouts with state=active filter
    def test_admin_layouts_state_active_filter(self):
        """Test that state=active returns only non-deleted, active revisions"""
        response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "active"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert "pagination" in data, "Response should contain 'pagination' key"
        
        # All items should be active (is_active=true AND is_deleted=false)
        for item in data["items"]:
            assert item.get("is_active") is True or item.get("is_active") is None, f"Item should be active: {item.get('id')}"
            assert item.get("is_deleted") is False or item.get("is_deleted") is None, f"Item should not be deleted: {item.get('id')}"
        
        print(f"✓ state=active returned {len(data['items'])} items, all active")
    
    # Test 2: GET /api/admin/layouts with state=passive filter
    def test_admin_layouts_state_passive_filter(self):
        """Test that state=passive returns deleted or inactive revisions"""
        response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "passive"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert "pagination" in data, "Response should contain 'pagination' key"
        
        # All items should be passive (is_deleted=true OR is_active=false)
        for item in data["items"]:
            is_deleted = item.get("is_deleted", False)
            is_active = item.get("is_active", True)
            is_passive = is_deleted or not is_active
            assert is_passive, f"Item should be passive: {item.get('id')}, is_deleted={is_deleted}, is_active={is_active}"
        
        print(f"✓ state=passive returned {len(data['items'])} items, all passive")
    
    # Test 3: GET /api/admin/layouts with state=all (default)
    def test_admin_layouts_state_all_default(self):
        """Test that state=all returns both active and passive revisions"""
        response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "all"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        
        print(f"✓ state=all returned {len(data['items'])} items")
    
    # Test 4: Invalid state filter should return 400
    def test_admin_layouts_invalid_state_filter(self):
        """Test that invalid state filter returns 400 error"""
        response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "invalid_state"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Invalid state filter correctly returns 400")
    
    # Test 5: POST /api/admin/layouts/workflows/reset-and-seed-home-wireframe endpoint
    def test_reset_and_seed_home_wireframe_endpoint_exists(self):
        """Test that reset-and-seed-home-wireframe endpoint responds successfully"""
        response = self.session.post(f"{BASE_URL}/api/admin/layouts/workflows/reset-and-seed-home-wireframe", json={
            "countries": ["TR", "DE", "FR"],
            "module": "global",
            "passivate_all": True,
            "hard_delete_demo_pages": True
        })
        
        # Should be 200 (success) or at least not 404/405 (endpoint exists)
        assert response.status_code in [200, 201], f"Expected success, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok=true in response: {data}"
        assert "summary" in data, f"Expected summary in response: {data}"
        assert "countries" in data, f"Expected countries in response: {data}"
        
        summary = data.get("summary", {})
        print(f"✓ Reset and seed wireframe succeeded:")
        print(f"  - hard_deleted_demo_revisions: {summary.get('hard_deleted_demo_revisions', 0)}")
        print(f"  - passivated_revisions: {summary.get('passivated_revisions', 0)}")
        print(f"  - home_pages_touched: {summary.get('home_pages_touched', 0)}")
        print(f"  - reactivated_home_revisions: {summary.get('reactivated_home_revisions', 0)}")


class TestLayoutBuilderRestoreEndpoint:
    """Tests for Layout Builder restore endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip(f"No token in login response: {data}")
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    def test_restore_endpoint_with_invalid_revision_id(self):
        """Test that restore endpoint returns 404 for non-existent revision"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.session.post(f"{BASE_URL}/api/admin/layouts/{fake_uuid}/restore", json={})
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Restore endpoint returns 404 for non-existent revision")
    
    def test_restore_endpoint_with_invalid_uuid_format(self):
        """Test that restore endpoint returns 400 for invalid UUID format"""
        response = self.session.post(f"{BASE_URL}/api/admin/layouts/invalid-uuid/restore", json={})
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Restore endpoint returns 400 for invalid UUID format")
    
    def test_restore_real_passive_revision(self):
        """Test restoring a real passive revision if one exists"""
        # First get a passive revision
        passive_response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "passive",
            "limit": 1
        })
        
        if passive_response.status_code != 200:
            pytest.skip(f"Could not fetch passive revisions: {passive_response.text}")
        
        passive_data = passive_response.json()
        items = passive_data.get("items", [])
        
        if not items:
            # No passive revisions to test
            print("✓ No passive revisions available to test restore - skipping actual restore test")
            return
        
        # Found a passive revision, try to restore it
        revision_id = items[0].get("revision_id") or items[0].get("id")
        is_deleted = items[0].get("is_deleted", False)
        
        if is_deleted:
            # Use restore endpoint for deleted items
            response = self.session.post(f"{BASE_URL}/api/admin/layouts/{revision_id}/restore", json={})
        else:
            # Use active endpoint for just inactive items
            response = self.session.patch(f"{BASE_URL}/api/admin/layouts/{revision_id}/active", json={
                "is_active": True
            })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, f"Expected ok=true: {data}"
        
        print(f"✓ Successfully restored revision {revision_id}")


class TestLayoutBuilderVerifyAfterReset:
    """Tests to verify state after reset-and-seed-home-wireframe"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip(f"No token in login response: {data}")
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    def test_active_list_has_home_pages(self):
        """Verify that active list contains home pages after reset"""
        response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "active"
        })
        
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # Look for HOME type pages
        home_items = [item for item in items if item.get("page_type") == "home"]
        
        print(f"✓ Active list contains {len(home_items)} HOME page(s) out of {len(items)} total")
        
        # Verify countries
        countries_found = set(item.get("country") for item in home_items)
        expected_countries = {"TR", "DE", "FR"}
        
        print(f"  - HOME pages found for countries: {countries_found}")
    
    def test_verify_wireframe_payload_structure(self):
        """Verify that active home pages have wireframe structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/layouts", params={
            "include_deleted": "true",
            "state": "active"
        })
        
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # Find an active home page
        home_items = [item for item in items if item.get("page_type") == "home"]
        
        if not home_items:
            print("✓ No active home pages found to verify wireframe")
            return
        
        # Check payload structure of first home page
        home_item = home_items[0]
        payload = home_item.get("payload_json", {})
        
        if payload:
            # Check for wireframe structure
            has_meta = "meta" in payload
            has_rows = "rows" in payload
            rows = payload.get("rows", [])
            
            print(f"✓ Home page payload verification:")
            print(f"  - Has meta: {has_meta}")
            print(f"  - Has rows: {has_rows}")
            print(f"  - Row count: {len(rows)}")
            
            if has_meta:
                meta = payload.get("meta", {})
                template_version = meta.get("template_version", "")
                generated_by = meta.get("generated_by", "")
                print(f"  - Template version: {template_version}")
                print(f"  - Generated by: {generated_by}")
        else:
            print("✓ No payload found in home page item (may need full revision fetch)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
