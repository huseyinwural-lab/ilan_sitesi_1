"""
Test suite for Category Navigator cleanup verification.
Verifies:
1. Backend API no longer returns deprecated navigator keys
2. Backend API returns new navigator keys
3. Data reports exist for cleanup operations
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"

# Deprecated keys that should NOT exist
DEPRECATED_KEYS = [
    'category.navigator',
    'layout.category-navigator-side',
    'layout.category-navigator-top'
]

# New keys that SHOULD exist
NEW_KEYS = [
    'layout.category-navigator-main-side',
    'layout.category-navigator-category-side'
]

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated API client session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestCategoryNavigatorComponentDefinitions:
    """Tests for /api/admin/site/content-layout/components endpoint"""
    
    def test_components_endpoint_returns_200(self, api_client):
        """Verify components endpoint is accessible"""
        response = api_client.get(f"{BASE_URL}/api/admin/site/content-layout/components?page=1&limit=100&is_active=true")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_deprecated_keys_not_returned(self, api_client):
        """Verify deprecated navigator keys are NOT in the response"""
        response = api_client.get(f"{BASE_URL}/api/admin/site/content-layout/components?page=1&limit=100&is_active=true")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get('items', [])
        all_keys = [item.get('key') for item in items]
        
        for deprecated_key in DEPRECATED_KEYS:
            assert deprecated_key not in all_keys, f"Deprecated key '{deprecated_key}' should NOT be in response"
    
    def test_new_keys_returned(self, api_client):
        """Verify new navigator keys ARE in the response"""
        response = api_client.get(f"{BASE_URL}/api/admin/site/content-layout/components?page=1&limit=100&is_active=true")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get('items', [])
        all_keys = [item.get('key') for item in items]
        
        for new_key in NEW_KEYS:
            assert new_key in all_keys, f"New key '{new_key}' should be in response"
    
    def test_only_two_navigator_keys_exist(self, api_client):
        """Verify exactly 2 navigator-related keys exist (the new ones)"""
        response = api_client.get(f"{BASE_URL}/api/admin/site/content-layout/components?page=1&limit=100&is_active=true")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get('items', [])
        navigator_keys = [item.get('key') for item in items if 'navigator' in (item.get('key') or '').lower()]
        
        assert len(navigator_keys) == 2, f"Expected 2 navigator keys, found {len(navigator_keys)}: {navigator_keys}"
        assert set(navigator_keys) == set(NEW_KEYS), f"Navigator keys mismatch: {navigator_keys}"


class TestCategoryTreeAPI:
    """Tests for category tree API used by navigators"""
    
    def test_category_tree_endpoint_returns_200(self):
        """Verify category tree endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&depth=L1")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_category_tree_returns_items_for_de(self):
        """Verify DE country has categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&depth=L1")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get('items', [])
        assert len(items) > 0, "Expected non-empty category tree for DE"
    
    def test_category_tree_depth_lall(self):
        """Verify Lall depth returns nested children"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&depth=Lall")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get('items', [])
        assert len(items) > 0, "Expected non-empty category tree"
        
        # Check at least one item has children
        has_children = any(len(item.get('children', [])) > 0 for item in items)
        assert has_children, "Expected at least one category with children in Lall depth"


class TestCleanupDataReports:
    """Tests for cleanup data report files"""
    
    def test_category_cleanup_revert_result_exists(self):
        """Verify category cleanup report exists"""
        import json
        report_path = "/app/test_reports/category_cleanup_revert_result.json"
        assert os.path.exists(report_path), f"Report file not found: {report_path}"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        # Verify expected fields
        assert 'deleted_seed_categories' in data, "Missing 'deleted_seed_categories' field"
        assert data['deleted_seed_categories'] > 0, "Expected some categories to be deleted"
    
    def test_layout_navigator_cleanup_result_exists(self):
        """Verify layout navigator cleanup report exists"""
        import json
        report_path = "/app/test_reports/layout_category_navigator_cleanup_result.json"
        assert os.path.exists(report_path), f"Report file not found: {report_path}"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        # Verify cleanup was performed
        assert 'revisions_updated' in data, "Missing 'revisions_updated' field"
    
    def test_component_definition_sync_result_exists(self):
        """Verify component definition sync report exists"""
        import json
        report_path = "/app/test_reports/component_definition_sync_result.json"
        assert os.path.exists(report_path), f"Report file not found: {report_path}"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        # Verify new components were upserted
        assert 'new_upserted' in data, "Missing 'new_upserted' field"
        upserted = data['new_upserted']
        upserted_keys = [item.get('key') for item in upserted if isinstance(item, dict)]
        
        for new_key in NEW_KEYS:
            assert new_key in upserted_keys, f"New key '{new_key}' should be in upserted list"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
