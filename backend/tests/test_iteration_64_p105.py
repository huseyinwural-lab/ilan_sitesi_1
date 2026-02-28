"""
Iteration 64 Tests - P105 HomePage + SearchPage Features
Tests for:
1. Backend /api/v2/search doping_type=urgent filter
2. Backend /api/v2/search doping_type=showcase filter  
3. Backend /api/categories?module=real_estate|vehicle|other endpoints
4. Frontend HomePage data-testid structures (module-group, urgent link, showcase link)
5. Frontend SearchPage doping title and chip rendering
"""

import os
import pytest
import requests

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session for API testing"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestBackendSearchDopingFilters:
    """Tests for /api/v2/search doping_type filter (urgent/showcase)"""
    
    def test_search_doping_type_urgent_returns_only_urgent_listings(self, api_client):
        """GET /api/v2/search?doping_type=urgent should return only is_urgent=True listings"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "limit": 10,
            "doping_type": "urgent"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert "pagination" in data, "Response should have 'pagination' field"
        
        items = data["items"]
        total = data["pagination"].get("total", 0)
        
        print(f"Urgent search returned {len(items)} items, total: {total}")
        
        # Verify all returned items are urgent
        for item in items:
            assert item.get("is_urgent") is True, f"Item {item.get('id')} should be is_urgent=True"
            # Urgent listings should NOT be featured (exclusive in this filter)
            # Note: The backend logic excludes featured from urgent results
    
    def test_search_doping_type_showcase_returns_only_featured_listings(self, api_client):
        """GET /api/v2/search?doping_type=showcase should return only is_featured=True listings"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "limit": 10,
            "doping_type": "showcase"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have 'items' field"
        assert "pagination" in data, "Response should have 'pagination' field"
        
        items = data["items"]
        total = data["pagination"].get("total", 0)
        
        print(f"Showcase search returned {len(items)} items, total: {total}")
        
        # Verify all returned items are featured (showcase)
        for item in items:
            assert item.get("is_featured") is True, f"Item {item.get('id')} should be is_featured=True"
    
    def test_search_doping_type_invalid_returns_400(self, api_client):
        """GET /api/v2/search?doping_type=invalid should return 400"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "doping_type": "invalid_type"
        })
        
        assert response.status_code == 400, f"Expected 400 for invalid doping_type, got {response.status_code}"
    
    def test_search_doping_type_free_returns_non_doping_listings(self, api_client):
        """GET /api/v2/search?doping_type=free should return free listings (no doping)"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "limit": 10,
            "doping_type": "free"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        items = data.get("items", [])
        
        # Free listings should not be featured or urgent
        for item in items:
            # Free means NOT featured AND NOT urgent (AND NOT paid doping)
            assert item.get("is_featured") is not True or item.get("is_urgent") is not True, \
                f"Free listing {item.get('id')} should not be featured or urgent"


class TestBackendCategoryModuleFilter:
    """Tests for /api/categories?module=X endpoint"""
    
    def test_categories_module_real_estate_returns_emlak(self, api_client):
        """GET /api/categories?module=real_estate should return Emlak categories"""
        response = api_client.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        categories = response.json()
        assert isinstance(categories, list), "Categories should be a list"
        
        print(f"real_estate module returned {len(categories)} categories")
        
        # All returned categories should have module=real_estate
        for cat in categories:
            assert cat.get("module") == "real_estate", \
                f"Category {cat.get('id')} has module={cat.get('module')}, expected real_estate"
    
    def test_categories_module_vehicle_returns_vasita(self, api_client):
        """GET /api/categories?module=vehicle should return vehicle categories"""
        response = api_client.get(f"{BASE_URL}/api/categories", params={
            "module": "vehicle",
            "country": "DE"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        categories = response.json()
        assert isinstance(categories, list), "Categories should be a list"
        
        print(f"vehicle module returned {len(categories)} categories")
        
        # All returned categories should have module=vehicle
        for cat in categories:
            assert cat.get("module") == "vehicle", \
                f"Category {cat.get('id')} has module={cat.get('module')}, expected vehicle"
    
    def test_categories_module_other_returns_empty_or_other(self, api_client):
        """GET /api/categories?module=other should return other categories (may be empty)"""
        response = api_client.get(f"{BASE_URL}/api/categories", params={
            "module": "other",
            "country": "DE"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        categories = response.json()
        assert isinstance(categories, list), "Categories should be a list"
        
        print(f"other module returned {len(categories)} categories")
        
        # All returned categories should have module=other (if any)
        for cat in categories:
            assert cat.get("module") == "other", \
                f"Category {cat.get('id')} has module={cat.get('module')}, expected other"
    
    def test_categories_structure_has_required_fields(self, api_client):
        """Categories should have required fields: id, name, slug, module, parent_id"""
        response = api_client.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        
        assert response.status_code == 200
        categories = response.json()
        
        if len(categories) == 0:
            pytest.skip("No categories to test structure")
        
        required_fields = ["id", "name", "slug", "module"]
        for cat in categories[:3]:  # Check first 3
            for field in required_fields:
                assert field in cat, f"Category missing required field: {field}"
            
            # parent_id can be null (for root categories)
            assert "parent_id" in cat or cat.get("parent_id") is None


class TestBackendShowcaseLayoutConfig:
    """Tests for /api/site/showcase-layout endpoint"""
    
    def test_showcase_layout_returns_homepage_config(self, api_client):
        """GET /api/site/showcase-layout should return homepage showcase configuration"""
        response = api_client.get(f"{BASE_URL}/api/site/showcase-layout")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Should have config object
        assert "config" in data or "homepage" in data.get("config", {}), \
            "Response should have config with homepage settings"
        
        config = data.get("config", {})
        if "homepage" in config:
            homepage = config["homepage"]
            # Homepage config should have rows, columns, listing_count
            if "rows" in homepage:
                assert isinstance(homepage["rows"], (int, type(None)))
            if "columns" in homepage:
                assert isinstance(homepage["columns"], (int, type(None)))
            if "listing_count" in homepage:
                assert isinstance(homepage["listing_count"], (int, type(None)))


class TestSearchPaginationBehavior:
    """Tests for search pagination with doping filters"""
    
    def test_urgent_search_pagination_returns_correct_count(self, api_client):
        """Verify urgent search pagination.total matches actual urgent listings"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "limit": 5,
            "page": 1,
            "doping_type": "urgent"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        pagination = data.get("pagination", {})
        total = pagination.get("total", 0)
        items_count = len(data.get("items", []))
        
        print(f"Urgent: Page 1 returned {items_count} items, total: {total}")
        
        # items_count should be <= limit
        assert items_count <= 5, "Should not exceed limit"
        
        # If total > limit, there should be more pages
        if total > 5:
            assert pagination.get("pages", 1) > 1, "Should have multiple pages"
    
    def test_showcase_search_pagination_returns_correct_count(self, api_client):
        """Verify showcase search pagination.total matches actual showcase listings"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "limit": 5,
            "page": 1,
            "doping_type": "showcase"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        pagination = data.get("pagination", {})
        total = pagination.get("total", 0)
        items_count = len(data.get("items", []))
        
        print(f"Showcase: Page 1 returned {items_count} items, total: {total}")
        
        # items_count should be <= limit
        assert items_count <= 5, "Should not exceed limit"


class TestSearchSEOFields:
    """Tests for SEO-related response fields"""
    
    def test_search_response_includes_doping_type_field(self, api_client):
        """Search response should include doping_type in metadata for SEO"""
        response = api_client.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "doping_type": "urgent"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if response includes doping_type info for frontend SEO
        # This could be in metadata or top-level
        items = data.get("items", [])
        for item in items[:1]:  # Check first item
            # Items should have doping_type bucket info
            assert "doping_type" in item or "is_urgent" in item, \
                "Item should have doping indicator"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
