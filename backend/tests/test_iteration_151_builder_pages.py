"""
Iteration 151: Content Builder Pages & Publish Guard Tests

Tests:
1. Content Layout Resolve API for different page types (home, urgent_listings, category_l0_l1, search_ln)
2. Publish Guard - blocked deprecated component keys
3. Admin component definitions - deprecated keys excluded, new navigator keys present
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://page-builder-stable.preview.emergentagent.com").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"

# Deprecated component keys that should be blocked
DEPRECATED_CATEGORY_NAVIGATOR_KEYS = [
    "category.navigator",
    "layout.category-navigator-side",
    "layout.category-navigator-top",
]

# New navigator keys that should be present
NEW_NAVIGATOR_KEYS = [
    "layout.category-navigator-main-side",
    "layout.category-navigator-category-side",
]

# All blocked keys for publish guard
PUBLISH_GUARD_BLOCKED_KEYS = [
    "category.navigator",
    "layout.category-navigator-side",
    "layout.category-navigator-top",
    "home.default-content",
    "search.l1.default-content",
    "search.l2.default-content",
]


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    data = response.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        pytest.skip("No token in login response")
    return token


@pytest.fixture
def admin_headers(admin_token):
    """Get admin headers with auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestContentLayoutResolve:
    """Test Content Layout Resolve API for different countries/page types"""
    
    @pytest.mark.parametrize("country", ["TR", "DE", "FR"])
    def test_home_layout_resolve(self, country):
        """Test resolve API for home page type - should return layout or empty state (not static HTML)"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": country,
                "module": "global",
                "page_type": "home"
            },
            timeout=60
        )
        
        # 200 = found layout, 404 = not found, 409 = no published revision
        assert response.status_code in [200, 404, 409], f"Unexpected status {response.status_code} for {country} home"
        
        if response.status_code == 200:
            data = response.json()
            # If found, should have revision with payload_json
            if data.get("revision"):
                assert "payload_json" in data["revision"], "Layout should have payload_json"
                payload = data["revision"]["payload_json"]
                # Payload should have rows structure (builder-driven)
                if payload:
                    assert "rows" in payload or payload == {}, f"Payload should be builder format for {country}"
                print(f"✓ {country} home: Found builder layout with {len(payload.get('rows', []))} rows")
            else:
                print(f"✓ {country} home: Empty layout (will show empty-state)")
        elif response.status_code == 409:
            print(f"✓ {country} home: No published revision (409) - will show empty-state")
        else:
            print(f"✓ {country} home: No layout (404) - will show empty-state")
    
    @pytest.mark.parametrize("country", ["TR", "DE", "FR"])
    def test_urgent_listings_layout_resolve(self, country):
        """Test resolve API for urgent_listings page type - should be builder driven"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": country,
                "module": "global",
                "page_type": "urgent_listings"
            },
            timeout=60
        )
        
        # 200 = found, 404 = not found, 409 = no published revision (all valid builder-driven responses)
        assert response.status_code in [200, 404, 409], f"Unexpected status {response.status_code} for {country} urgent_listings"
        
        if response.status_code == 200:
            data = response.json()
            if data.get("revision") and data["revision"].get("payload_json"):
                payload = data["revision"]["payload_json"]
                print(f"✓ {country} urgent_listings: Found builder layout with {len(payload.get('rows', []))} rows")
            else:
                print(f"✓ {country} urgent_listings: Empty layout")
        elif response.status_code == 409:
            print(f"✓ {country} urgent_listings: No published revision (409) - will show empty-state")
        else:
            print(f"✓ {country} urgent_listings: No layout (404) - will show empty-state")
    
    @pytest.mark.parametrize("country", ["TR", "DE", "FR"])
    def test_category_l0_l1_layout_resolve(self, country):
        """Test resolve API for category_l0_l1 page type"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": country,
                "module": "global",
                "page_type": "category_l0_l1"
            },
            timeout=60
        )
        
        assert response.status_code in [200, 404, 409], f"Unexpected status {response.status_code} for {country} category_l0_l1"
        
        if response.status_code == 200:
            data = response.json()
            if data.get("revision") and data["revision"].get("payload_json"):
                payload = data["revision"]["payload_json"]
                print(f"✓ {country} category_l0_l1: Found builder layout with {len(payload.get('rows', []))} rows")
            else:
                print(f"✓ {country} category_l0_l1: Empty layout")
        elif response.status_code == 409:
            print(f"✓ {country} category_l0_l1: No published revision (409) - will show empty-state")
        else:
            print(f"✓ {country} category_l0_l1: No layout (404) - will show empty-state")
    
    @pytest.mark.parametrize("country", ["TR", "DE", "FR"])
    def test_search_ln_layout_resolve(self, country):
        """Test resolve API for search_ln page type"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": country,
                "module": "global",
                "page_type": "search_ln"
            },
            timeout=60
        )
        
        assert response.status_code in [200, 404, 409], f"Unexpected status {response.status_code} for {country} search_ln"
        
        if response.status_code == 200:
            data = response.json()
            if data.get("revision") and data["revision"].get("payload_json"):
                payload = data["revision"]["payload_json"]
                print(f"✓ {country} search_ln: Found builder layout with {len(payload.get('rows', []))} rows")
            else:
                print(f"✓ {country} search_ln: Empty layout")
        elif response.status_code == 409:
            print(f"✓ {country} search_ln: No published revision (409) - will show empty-state")
        else:
            print(f"✓ {country} search_ln: No layout (404) - will show empty-state")


class TestPublishGuard:
    """Test Publish Guard - should block deprecated/unknown component keys"""
    
    def test_publish_guard_blocks_deprecated_keys(self, admin_headers):
        """Test that publish guard blocks deprecated component keys"""
        # First get layout pages using correct API endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            params={"country": "TR", "page_type": "home"},
            timeout=30
        )
        
        if response.status_code != 200:
            pytest.skip(f"Cannot get layout pages: {response.status_code}")
        
        pages = response.json()
        items = pages.get("items", pages) if isinstance(pages, dict) else pages
        if not items:
            pytest.skip("No layout pages to test publish guard")
        
        # Get first page
        test_page = items[0] if isinstance(items, list) else items
        page_id = test_page.get("id") or test_page.get("layout_page_id")
        
        if not page_id:
            pytest.skip("No page ID found")
        
        # Test with deprecated key
        deprecated_key = "category.navigator"
        draft_payload = {
            "payload_json": {
                "rows": [
                    {
                        "id": "test-row-1",
                        "columns": [
                            {
                                "id": "test-col-1",
                                "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                "components": [
                                    {
                                        "id": "test-comp-1",
                                        "key": deprecated_key,
                                        "props": {},
                                        "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        # Create/update draft using correct API endpoint
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json=draft_payload,
            timeout=30
        )
        
        assert draft_response.status_code in [200, 201], f"Draft creation failed: {draft_response.status_code}"
        
        draft_data = draft_response.json()
        item = draft_data.get("item", draft_data)
        revision_id = item.get("id") or item.get("revision_id")
        
        assert revision_id, "No revision_id in draft response"
        
        # Try to publish - should be blocked
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{revision_id}/publish",
            headers=admin_headers,
            timeout=30
        )
        
        # Should return 400 with publish_guard_blocked_components
        assert publish_response.status_code == 400, f"Expected 400, got {publish_response.status_code}"
        detail = publish_response.json().get("detail", {})
        assert isinstance(detail, dict), "Expected detail to be a dict"
        assert detail.get("code") == "publish_guard_blocked_components", f"Expected publish_guard_blocked_components, got {detail}"
        blocked_keys = detail.get("blocked_keys", [])
        assert deprecated_key in blocked_keys, f"Expected {deprecated_key} in blocked_keys"
        print(f"✓ Publish guard correctly blocked deprecated key: {deprecated_key}")
    
    def test_publish_guard_blocks_unknown_keys(self, admin_headers):
        """Test that publish guard blocks unknown/inactive component keys"""
        # Get layout pages using correct API endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            params={"country": "TR", "page_type": "home"},
            timeout=30
        )
        
        if response.status_code != 200:
            pytest.skip(f"Cannot get layout pages: {response.status_code}")
        
        pages = response.json()
        items = pages.get("items", pages) if isinstance(pages, dict) else pages
        if not items:
            pytest.skip("No layout pages to test")
        
        test_page = items[0] if isinstance(items, list) else items
        page_id = test_page.get("id") or test_page.get("layout_page_id")
        
        if not page_id:
            pytest.skip("No page ID found")
        
        # Test with unknown key
        unknown_key = "totally.unknown.component.test123"
        draft_payload = {
            "payload_json": {
                "rows": [
                    {
                        "id": "test-row-unknown",
                        "columns": [
                            {
                                "id": "test-col-unknown",
                                "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                "components": [
                                    {
                                        "id": "test-comp-unknown",
                                        "key": unknown_key,
                                        "props": {},
                                        "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json=draft_payload,
            timeout=30
        )
        
        assert draft_response.status_code in [200, 201], f"Draft creation failed: {draft_response.status_code}"
        
        draft_data = draft_response.json()
        item = draft_data.get("item", draft_data)
        revision_id = item.get("id") or item.get("revision_id")
        
        assert revision_id, "No revision_id in draft response"
        
        # Try to publish - should be blocked
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{revision_id}/publish",
            headers=admin_headers,
            timeout=30
        )
        
        assert publish_response.status_code == 400, f"Expected 400, got {publish_response.status_code}"
        detail = publish_response.json().get("detail", {})
        assert isinstance(detail, dict), "Expected detail to be a dict"
        assert detail.get("code") == "publish_guard_unknown_or_inactive_components", f"Expected publish_guard_unknown_or_inactive_components, got {detail}"
        print(f"✓ Publish guard correctly blocked unknown key: {unknown_key}")


class TestAdminComponentDefinitions:
    """Test Admin Component Definitions API"""
    
    def test_admin_component_list_excludes_deprecated(self, admin_headers):
        """Test that admin component list does not include deprecated navigator keys"""
        # Use correct API endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            params={"limit": 100},
            timeout=30
        )
        
        assert response.status_code == 200, f"Failed to get component definitions: {response.status_code}"
        
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if not isinstance(items, list):
            items = [items]
        
        component_keys = [item.get("key") for item in items if item.get("key")]
        
        # Check deprecated keys are not in the list
        for deprecated_key in DEPRECATED_CATEGORY_NAVIGATOR_KEYS:
            assert deprecated_key not in component_keys, f"Deprecated key {deprecated_key} should not be in component list"
            print(f"✓ Deprecated key '{deprecated_key}' correctly excluded from component list")
    
    def test_admin_component_list_includes_new_navigators(self, admin_headers):
        """Test that admin component list includes new navigator keys"""
        # Use correct API endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            params={"limit": 100},
            timeout=30
        )
        
        assert response.status_code == 200, f"Failed to get component definitions: {response.status_code}"
        
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if not isinstance(items, list):
            items = [items]
        
        component_keys = [item.get("key") for item in items if item.get("key")]
        
        # Check new navigator keys are present
        for new_key in NEW_NAVIGATOR_KEYS:
            assert new_key in component_keys, f"New navigator key {new_key} should be in component list"
            print(f"✓ New navigator key '{new_key}' found in component list")


class TestPublicPageAPIs:
    """Test public page APIs return proper responses (no static HTML fallback)"""
    
    @pytest.mark.parametrize("path", ["/tr", "/de", "/fr"])
    def test_public_home_pages_load(self, path):
        """Test that public home pages load (TR/DE/FR)"""
        response = requests.get(
            f"{BASE_URL}{path}",
            allow_redirects=True,
            timeout=30
        )
        # Should return 200 or redirect
        assert response.status_code in [200, 301, 302], f"Failed to load {path}: {response.status_code}"
        print(f"✓ {path} loads successfully (status: {response.status_code})")
    
    @pytest.mark.parametrize("path", ["/tr/acil", "/de/acil", "/fr/acil"])
    def test_public_urgent_pages_load(self, path):
        """Test that public urgent pages load"""
        response = requests.get(
            f"{BASE_URL}{path}",
            allow_redirects=True,
            timeout=30
        )
        assert response.status_code in [200, 301, 302], f"Failed to load {path}: {response.status_code}"
        print(f"✓ {path} loads successfully (status: {response.status_code})")
    
    @pytest.mark.parametrize("path", ["/tr/search", "/de/search", "/fr/search"])
    def test_public_search_pages_load(self, path):
        """Test that public search pages load"""
        response = requests.get(
            f"{BASE_URL}{path}",
            allow_redirects=True,
            timeout=30
        )
        assert response.status_code in [200, 301, 302], f"Failed to load {path}: {response.status_code}"
        print(f"✓ {path} loads successfully (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
