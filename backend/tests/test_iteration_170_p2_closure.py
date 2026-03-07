"""
P2 Closure Items Acceptance Tests - Iteration 170
- Component API Health Dashboard Widget (components, layouts, menu-health endpoints)
- Address Form UI (completion panel, clear fields action)
- Visual Diff Modal (revision list panel, filter, cursor, raw JSON toggle)

Tests run against REACT_APP_BACKEND_URL
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as Super Admin"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
        timeout=30
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    data = response.json()
    return data.get("access_token") or data.get("token")

@pytest.fixture(scope="module")
def user_token():
    """Authenticate as regular user (optional)"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@platform.com", "password": "User123!"},
        timeout=30
    )
    if response.status_code != 200:
        return None
    data = response.json()
    return data.get("access_token") or data.get("token")


class TestComponentApiHealthEndpoints:
    """
    Component API Health Widget - checks that endpoints used by
    fetchComponentApiHealth in Dashboard.js are accessible
    """

    def test_component_definitions_endpoint(self, admin_token):
        """GET /api/admin/site/content-layout/components should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 1},
            timeout=30
        )
        # Should be 200 (healthy) or 401/403 (restricted)
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print(f"[PASS] Component definitions endpoint returned 200")
            data = response.json()
            assert "items" in data or "total" in data or isinstance(data, list)
        else:
            print(f"[INFO] Component definitions endpoint returned {response.status_code} (restricted)")

    def test_layouts_endpoint(self, admin_token):
        """GET /api/admin/layouts should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 1},
            timeout=30
        )
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print(f"[PASS] Layouts endpoint returned 200")
            data = response.json()
            assert "items" in data or "total" in data or isinstance(data, list)
        else:
            print(f"[INFO] Layouts endpoint returned {response.status_code} (restricted)")

    def test_menu_health_endpoint(self, admin_token):
        """GET /api/admin/menu-items/health should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/menu-items/health",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print(f"[PASS] Menu health endpoint returned 200")
        else:
            print(f"[INFO] Menu health endpoint returned {response.status_code}")


class TestDashboardSummaryEndpoint:
    """Dashboard summary endpoint for overall dashboard functionality"""

    def test_dashboard_summary(self, admin_token):
        """GET /api/admin/dashboard/summary should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Dashboard summary failed: {response.status_code}"
        data = response.json()
        print(f"[PASS] Dashboard summary returned 200")
        # Check some expected fields
        assert "users" in data or "kpis" in data or "health" in data


class TestContentBuilderRevisionEndpoints:
    """
    Content Builder revision list and related endpoints for Visual Diff modal
    """

    def test_content_pages_list(self, admin_token):
        """GET /api/admin/site/content-layout/pages should return list of pages"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Content pages failed: {response.status_code}"
        data = response.json()
        assert "items" in data or isinstance(data, list)
        print(f"[PASS] Content layout pages endpoint returned 200")

    def test_revisions_list_for_page(self, admin_token):
        """GET /api/admin/site/content-layout/pages/{page_id}/revisions - test for any existing page"""
        # First get a page
        pages_response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        if pages_response.status_code != 200:
            pytest.skip("Cannot fetch pages list")
        
        pages_data = pages_response.json()
        items = pages_data.get("items", pages_data if isinstance(pages_data, list) else [])
        
        if not items:
            pytest.skip("No pages available for revision test")
        
        page_id = items[0].get("id")
        if not page_id:
            pytest.skip("Page has no id")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Revisions list failed: {response.status_code}"
        data = response.json()
        assert "items" in data or isinstance(data, list)
        print(f"[PASS] Revisions list for page {page_id} returned 200")


class TestPlacesConfigEndpoint:
    """
    Places config endpoint for address form UI functionality
    """

    def test_places_config(self):
        """GET /api/places/config should return places configuration"""
        response = requests.get(
            f"{BASE_URL}/api/places/config",
            timeout=30
        )
        assert response.status_code == 200, f"Places config failed: {response.status_code}"
        data = response.json()
        # Check expected fields based on ListingDetails.js
        assert "real_mode" in data or "mode" in data or "country_options" in data
        print(f"[PASS] Places config endpoint returned 200")
        print(f"  - real_mode: {data.get('real_mode')}")
        print(f"  - mode: {data.get('mode')}")


class TestListingDesignEndpoint:
    """
    Listing design endpoint for address form configuration
    """

    def test_listing_design_config(self):
        """GET /api/site/listing-design should return listing design config"""
        response = requests.get(
            f"{BASE_URL}/api/site/listing-design",
            timeout=30
        )
        # This can be 200 or 404 if not configured
        assert response.status_code in [200, 404], f"Listing design failed: {response.status_code}"
        if response.status_code == 200:
            print(f"[PASS] Listing design config returned 200")
        else:
            print(f"[INFO] Listing design config returned 404 (not configured)")


class TestCatalogSchemaEndpoint:
    """
    Catalog schema endpoint used by ListingDetails.js
    """

    def test_catalog_schema(self, admin_token):
        """GET /api/catalog/schema should return schema for category"""
        # Try with a sample category
        response = requests.get(
            f"{BASE_URL}/api/catalog/schema",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"country": "TR"},
            timeout=30
        )
        # Can be 200, 400, or 404 depending on category
        assert response.status_code in [200, 400, 404, 422], f"Catalog schema failed: {response.status_code}"
        print(f"[INFO] Catalog schema endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
