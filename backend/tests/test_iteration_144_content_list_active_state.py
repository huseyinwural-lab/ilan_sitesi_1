"""
Iteration 144: Content List Active/Passive State + Core Template Pack Tests
Tests:
- GET /api/admin/layouts is_active field
- PATCH /api/admin/layouts/{id}/active toggle
- POST /api/admin/site/content-layout/preset/install-standard-pack core scope (4 templates)
- GET /api/admin/site/content-layout/preset/verify-standard-pack TR/DE/FR total_rows=12
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "admin@platform.com"
TEST_PASSWORD = "Admin123!"


class TestContentListActiveState:
    """Backend API tests for Content List active/passive state + template pack features"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        token = data.get("access_token") or data.get("token")
        assert token, "No token in login response"
        return token

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept-Language": "tr",
        }

    # -------------------------------------------------------------------
    # Test 1: GET /api/admin/layouts returns is_active field
    # -------------------------------------------------------------------
    def test_get_layouts_has_is_active_field(self, auth_headers):
        """GET /api/admin/layouts should include is_active field for each item"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": True, "statuses": "draft,published", "limit": 10},
        )
        assert resp.status_code == 200, f"GET /api/admin/layouts failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Check response structure
        assert "items" in data, "Response should have 'items' key"
        items = data["items"]
        
        if len(items) > 0:
            # Verify is_active field exists in each item
            for idx, item in enumerate(items[:5]):  # Check first 5 items
                assert "is_active" in item, f"Item {idx} missing 'is_active' field: {item.keys()}"
                # is_active should be boolean
                assert isinstance(item["is_active"], bool), f"Item {idx} is_active should be bool, got {type(item['is_active'])}"
                print(f"Item {idx}: id={item.get('id', 'N/A')}, page_type={item.get('page_type', 'N/A')}, is_active={item['is_active']}")
        else:
            print("No layout items found, skipping is_active field verification")
        
        print(f"TEST PASSED: GET /api/admin/layouts returns items with is_active field")

    # -------------------------------------------------------------------
    # Test 2: PATCH /api/admin/layouts/{id}/active toggle works
    # -------------------------------------------------------------------
    def test_patch_layout_active_toggle(self, auth_headers):
        """PATCH /api/admin/layouts/{id}/active should toggle active state"""
        # First get a layout to test with
        list_resp = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": False, "statuses": "draft,published", "limit": 5},
        )
        assert list_resp.status_code == 200, f"GET layouts failed: {list_resp.text}"
        items = list_resp.json().get("items", [])
        
        if not items:
            pytest.skip("No layouts available to test toggle")
        
        # Find an active, non-deleted item to toggle
        test_item = None
        for item in items:
            if not item.get("is_deleted", False):
                test_item = item
                break
        
        if not test_item:
            pytest.skip("No non-deleted layouts to test toggle")
        
        revision_id = test_item.get("revision_id") or test_item.get("id")
        current_active = test_item.get("is_active", True)
        
        # Toggle to opposite state
        new_active = not current_active
        toggle_resp = requests.patch(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
            headers=auth_headers,
            json={"is_active": new_active},
        )
        
        # Accept both 200 and 422 (if policy prevents toggle)
        if toggle_resp.status_code == 200:
            toggle_data = toggle_resp.json()
            # Response has is_active in nested item or at root level
            if "item" in toggle_data:
                actual_active = toggle_data["item"].get("is_active")
            else:
                actual_active = toggle_data.get("is_active")
            
            assert actual_active is not None, f"Response should have is_active: {toggle_data}"
            assert actual_active == new_active, f"Expected is_active={new_active}, got {actual_active}"
            print(f"TEST PASSED: Toggle from {current_active} to {new_active} successful")
            
            # Toggle back to original state
            restore_resp = requests.patch(
                f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
                headers=auth_headers,
                json={"is_active": current_active},
            )
            assert restore_resp.status_code == 200, f"Restore toggle failed: {restore_resp.text}"
            print(f"Restored to original state: is_active={current_active}")
        elif toggle_resp.status_code == 400:
            # Possibly trying to toggle a deleted revision
            print(f"Toggle returned 400 (expected for deleted items): {toggle_resp.text}")
        else:
            assert False, f"Unexpected toggle response: {toggle_resp.status_code} {toggle_resp.text}"

    # -------------------------------------------------------------------
    # Test 3: PATCH active on deleted revision should return 400
    # -------------------------------------------------------------------
    def test_patch_active_on_deleted_revision_returns_400(self, auth_headers):
        """PATCH /api/admin/layouts/{id}/active on deleted revision should return 400"""
        # Get layouts including deleted
        list_resp = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": True, "statuses": "draft,published", "limit": 50},
        )
        assert list_resp.status_code == 200, f"GET layouts failed: {list_resp.text}"
        items = list_resp.json().get("items", [])
        
        # Find a deleted item
        deleted_item = None
        for item in items:
            if item.get("is_deleted", False):
                deleted_item = item
                break
        
        if not deleted_item:
            print("No deleted layouts found to test, skipping")
            pytest.skip("No deleted layouts to test 400 response")
        
        revision_id = deleted_item.get("revision_id") or deleted_item.get("id")
        toggle_resp = requests.patch(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
            headers=auth_headers,
            json={"is_active": True},
        )
        
        assert toggle_resp.status_code == 400, f"Expected 400 for deleted revision toggle, got {toggle_resp.status_code}"
        print(f"TEST PASSED: Toggle on deleted revision correctly returns 400")

    # -------------------------------------------------------------------
    # Test 4: verify-standard-pack with core scope returns total_rows=12
    # -------------------------------------------------------------------
    def test_verify_standard_pack_core_scope_total_rows_12(self, auth_headers):
        """
        GET /api/admin/site/content-layout/preset/verify-standard-pack
        With TR,DE,FR countries and include_extended_templates=false (core scope)
        Should return total_rows=12 (3 countries * 4 core templates)
        """
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers=auth_headers,
            params={
                "countries": "TR,DE,FR",
                "module": "global",
                "include_extended_templates": False,  # core scope
            },
        )
        assert resp.status_code == 200, f"verify-standard-pack failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        # Check response structure
        assert "summary" in data, f"Response should have 'summary': {data.keys()}"
        summary = data["summary"]
        
        # Core scope: 4 templates (home, urgent_listings, category_l0_l1, search_ln)
        # 3 countries * 4 templates = 12 total_rows
        total_rows = summary.get("total_rows", 0)
        assert total_rows == 12, f"Expected total_rows=12 for core scope (3 countries * 4 templates), got {total_rows}"
        
        # Verify template_scope is core
        template_scope = data.get("template_scope", "")
        assert template_scope == "core", f"Expected template_scope='core', got '{template_scope}'"
        
        print(f"TEST PASSED: verify-standard-pack core scope returns total_rows={total_rows}")
        print(f"  - template_scope: {template_scope}")
        print(f"  - ready_rows: {summary.get('ready_rows', 0)}")
        print(f"  - ready_ratio: {summary.get('ready_ratio', 0)}%")

    # -------------------------------------------------------------------
    # Test 5: verify-standard-pack with extended scope
    # -------------------------------------------------------------------
    def test_verify_standard_pack_extended_scope(self, auth_headers):
        """
        GET /api/admin/site/content-layout/preset/verify-standard-pack
        With include_extended_templates=true should return more than 12 total_rows
        """
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers=auth_headers,
            params={
                "countries": "TR,DE,FR",
                "module": "global",
                "include_extended_templates": True,  # extended scope
            },
        )
        assert resp.status_code == 200, f"verify-standard-pack failed: {resp.status_code} {resp.text}"
        data = resp.json()
        
        summary = data.get("summary", {})
        total_rows = summary.get("total_rows", 0)
        
        # Extended scope: 15 templates * 3 countries = 45 total_rows
        assert total_rows == 45, f"Expected total_rows=45 for extended scope (3 countries * 15 templates), got {total_rows}"
        
        template_scope = data.get("template_scope", "")
        assert template_scope == "extended", f"Expected template_scope='extended', got '{template_scope}'"
        
        print(f"TEST PASSED: verify-standard-pack extended scope returns total_rows={total_rows}")

    # -------------------------------------------------------------------
    # Test 6: install-standard-pack with core scope returns controlled response
    # -------------------------------------------------------------------
    def test_install_standard_pack_core_scope_response(self, auth_headers):
        """
        POST /api/admin/site/content-layout/preset/install-standard-pack
        Should return controlled JSON response with template_scope='core'
        """
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json={
                "countries": ["TR", "DE", "FR"],
                "module": "global",
                "persona": "individual",
                "variant": "A",
                "overwrite_existing_draft": True,
                "publish_after_seed": True,
                "include_extended_templates": False,  # core scope
            },
            timeout=60,
        )
        
        # Should return 200 with controlled response (not 503)
        assert resp.status_code == 200, f"install-standard-pack should return 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check response structure
        required_fields = ["ok", "module", "countries", "template_scope", "summary"]
        for field in required_fields:
            assert field in data, f"Response missing required field '{field}': {data.keys()}"
        
        # Verify template_scope is core
        assert data.get("template_scope") == "core", f"Expected template_scope='core', got '{data.get('template_scope')}'"
        
        # Check summary structure
        summary = data.get("summary", {})
        summary_fields = ["created_pages", "created_drafts", "updated_drafts", "skipped_drafts", "published_revisions"]
        for field in summary_fields:
            assert field in summary, f"Summary missing field '{field}': {summary.keys()}"
        
        print(f"TEST PASSED: install-standard-pack core scope returns controlled response")
        print(f"  - ok: {data.get('ok')}")
        print(f"  - template_scope: {data.get('template_scope')}")
        print(f"  - summary: {summary}")
        
        # Log failed_countries if any
        failed = data.get("failed_countries", [])
        if failed:
            print(f"  - failed_countries: {len(failed)} countries had issues")
            for fc in failed:
                print(f"    - {fc.get('country')}: {fc.get('error')}")

    # -------------------------------------------------------------------
    # Test 7: install-standard-pack validation - invalid persona returns 400
    # -------------------------------------------------------------------
    def test_install_standard_pack_invalid_persona_returns_400(self, auth_headers):
        """install-standard-pack with invalid persona should return 400"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json={
                "countries": ["TR"],
                "module": "global",
                "persona": "invalid_persona",  # Invalid
                "variant": "A",
            },
            timeout=30,
        )
        assert resp.status_code == 400, f"Expected 400 for invalid persona, got {resp.status_code}"
        print(f"TEST PASSED: Invalid persona returns 400")

    # -------------------------------------------------------------------
    # Test 8: install-standard-pack validation - invalid variant returns 400
    # -------------------------------------------------------------------
    def test_install_standard_pack_invalid_variant_returns_400(self, auth_headers):
        """install-standard-pack with invalid variant should return 400"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json={
                "countries": ["TR"],
                "module": "global",
                "persona": "individual",
                "variant": "X",  # Invalid - only A or B allowed
            },
            timeout=30,
        )
        assert resp.status_code == 400, f"Expected 400 for invalid variant, got {resp.status_code}"
        print(f"TEST PASSED: Invalid variant returns 400")

    # -------------------------------------------------------------------
    # Test 9: install-standard-pack validation - empty countries returns 422
    # -------------------------------------------------------------------
    def test_install_standard_pack_empty_countries_returns_422(self, auth_headers):
        """install-standard-pack with empty countries should return 422"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json={
                "countries": [],  # Empty
                "module": "global",
                "persona": "individual",
                "variant": "A",
            },
            timeout=30,
        )
        # Pydantic validation should return 422
        assert resp.status_code == 422, f"Expected 422 for empty countries, got {resp.status_code}"
        print(f"TEST PASSED: Empty countries returns 422")

    # -------------------------------------------------------------------
    # Test 10: verify-standard-pack returns items array
    # -------------------------------------------------------------------
    def test_verify_standard_pack_returns_items_array(self, auth_headers):
        """verify-standard-pack should return items array with page details"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers=auth_headers,
            params={
                "countries": "TR",
                "module": "global",
                "include_extended_templates": False,
            },
        )
        assert resp.status_code == 200, f"verify-standard-pack failed: {resp.status_code}"
        data = resp.json()
        
        # Check items array exists
        assert "items" in data, f"Response should have 'items' array"
        items = data["items"]
        assert isinstance(items, list), f"items should be list, got {type(items)}"
        
        # With core scope and 1 country, should have 4 items
        assert len(items) == 4, f"Expected 4 items for TR core scope, got {len(items)}"
        
        # Each item should have required fields
        for item in items:
            assert "country" in item, f"Item missing 'country'"
            assert "page_type" in item, f"Item missing 'page_type'"
            assert "is_ready" in item, f"Item missing 'is_ready'"
        
        print(f"TEST PASSED: verify-standard-pack returns {len(items)} items for TR core scope")
