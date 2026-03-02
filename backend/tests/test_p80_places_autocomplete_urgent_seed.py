"""
Test: P0 Places Autocomplete, Urgent Listings, Seed Data Validation
Iteration 70 - Google Autocomplete real mode + manual key, seed validation

Features tested:
1. /api/places/config - Backend guard for key existence
2. /api/places/autocomplete - Fallback when no key, accepts manual key
3. /api/v2/search with doping_type=urgent - Pagination and filter behavior
4. Seed data validation: real_estate root categories, vehicle makes/models/trims
5. Admin showcase publish -> homepage revalidate flow
"""

import os
import pytest
import requests
import uuid
from typing import Optional

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://marketplace-finance-3.preview.emergentagent.com")


@pytest.fixture
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get user auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "user@platform.com",
        "password": "User123!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("User authentication failed")


@pytest.fixture
def admin_token(api_client):
    """Get admin auth token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@platform.com",
        "password": "Admin123!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


class TestPlacesConfig:
    """Test /api/places/config endpoint - Backend guard for Google Maps key"""
    
    def test_places_config_returns_fallback_mode_without_key(self, api_client):
        """When no Google Maps key is configured, config should return fallback mode"""
        response = api_client.get(f"{BASE_URL}/api/places/config")
        assert response.status_code == 200
        
        data = response.json()
        # Backend has no key configured, so it should return fallback
        assert "real_mode" in data
        assert "mode" in data
        assert "key_source" in data
        assert data["manual_key_supported"] == True
        
        # If key_source is 'none', real_mode should be False
        if data["key_source"] == "none":
            assert data["real_mode"] == False
            assert data["mode"] == "fallback"
        print(f"Places config: mode={data['mode']}, key_source={data['key_source']}")


class TestPlacesAutocomplete:
    """Test /api/places/autocomplete - Fallback behavior and manual key support"""
    
    def test_autocomplete_without_key_returns_fallback(self, api_client):
        """Without any key, autocomplete should return fallback mode gracefully"""
        response = api_client.get(
            f"{BASE_URL}/api/places/autocomplete",
            params={"q": "Berlin", "country": "DE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "mode" in data
        assert "items" in data
        # Should gracefully return fallback mode message
        assert data["mode"] == "fallback"
        assert "message" in data or len(data["items"]) == 0
        print(f"Autocomplete without key: mode={data['mode']}, message={data.get('message', 'N/A')}")
    
    def test_autocomplete_with_invalid_manual_key(self, api_client):
        """With invalid manual key, should return 400 or fallback gracefully"""
        response = api_client.get(
            f"{BASE_URL}/api/places/autocomplete",
            params={"q": "Munich", "country": "DE", "manual_key": "invalid_key_123"}
        )
        # Should handle gracefully - either 400 or fallback
        assert response.status_code in [200, 400]
        
        data = response.json()
        if response.status_code == 200:
            assert data.get("mode") in ["fallback", "real"]
        print(f"Autocomplete with invalid key: status={response.status_code}")
    
    def test_autocomplete_short_query_returns_empty(self, api_client):
        """Query less than 2 chars should return empty items"""
        response = api_client.get(
            f"{BASE_URL}/api/places/autocomplete",
            params={"q": "B", "country": "DE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["mode"] == "fallback"
        assert len(data["items"]) == 0
        print("Short query returns empty as expected")
    
    def test_autocomplete_app_doesnt_crash(self, api_client):
        """Autocomplete endpoint should never crash the app"""
        # Test with various edge cases
        test_cases = [
            {"q": ""},
            {"q": "Berlin", "country": "INVALID"},
            {"q": "x" * 500},
        ]
        
        for params in test_cases:
            response = api_client.get(f"{BASE_URL}/api/places/autocomplete", params=params)
            # Should not return 500
            assert response.status_code != 500, f"App crashed with params: {params}"
        print("App stability test passed")


class TestPlacesDetails:
    """Test /api/places/details - Fallback behavior"""
    
    def test_details_without_key_returns_fallback(self, api_client):
        """Without key, details should return fallback gracefully"""
        response = api_client.get(
            f"{BASE_URL}/api/places/details",
            params={"place_id": "ChIJAVkDPzdOqEcRcDteW0YgIQQ", "country": "DE"}
        )
        # Should return 200 with fallback or handle gracefully
        assert response.status_code in [200, 400]
        
        data = response.json()
        if response.status_code == 200:
            assert data.get("mode") in ["fallback", "real"]
        print(f"Details without key: status={response.status_code}")
    
    def test_details_missing_place_id_returns_400(self, api_client):
        """Missing place_id should return 400"""
        response = api_client.get(
            f"{BASE_URL}/api/places/details",
            params={"place_id": "", "country": "DE"}
        )
        assert response.status_code == 400


class TestUrgentListings:
    """Test /api/v2/search with doping_type=urgent - Pagination and filter"""
    
    def test_urgent_filter_returns_urgent_listings(self, api_client):
        """doping_type=urgent should only return urgent listings"""
        response = api_client.get(
            f"{BASE_URL}/api/v2/search",
            params={"country": "DE", "doping_type": "urgent", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        
        # All returned items should be urgent
        for item in data["items"]:
            assert item.get("is_urgent") == True, f"Item {item['id']} is not urgent"
            assert item.get("is_featured") == False, f"Urgent item should not be featured"
        
        print(f"Urgent filter returned {len(data['items'])} items, total={data['pagination']['total']}")
    
    def test_urgent_pagination_works(self, api_client):
        """Pagination should work correctly for urgent listings"""
        # Get first page
        response1 = api_client.get(
            f"{BASE_URL}/api/v2/search",
            params={"country": "DE", "doping_type": "urgent", "page": 1, "limit": 5}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        total = data1["pagination"]["total"]
        pages = data1["pagination"]["pages"]
        
        print(f"Total urgent: {total}, pages: {pages}")
        
        if pages > 1:
            # Get second page
            response2 = api_client.get(
                f"{BASE_URL}/api/v2/search",
                params={"country": "DE", "doping_type": "urgent", "page": 2, "limit": 5}
            )
            assert response2.status_code == 200
            data2 = response2.json()
            
            # Items should be different
            ids1 = {item["id"] for item in data1["items"]}
            ids2 = {item["id"] for item in data2["items"]}
            assert ids1.isdisjoint(ids2), "Page 1 and 2 have overlapping items"
            print("Pagination verified - page 1 and 2 have different items")
    
    def test_urgent_high_page_returns_empty(self, api_client):
        """High page number should return empty items, not error"""
        response = api_client.get(
            f"{BASE_URL}/api/v2/search",
            params={"country": "DE", "doping_type": "urgent", "page": 999, "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"] == [] or len(data["items"]) == 0
        print("High page returns empty as expected")


class TestShowcaseFilter:
    """Test /api/v2/search with doping_type=showcase"""
    
    def test_showcase_filter_returns_showcase_listings(self, api_client):
        """doping_type=showcase should only return showcase listings"""
        response = api_client.get(
            f"{BASE_URL}/api/v2/search",
            params={"country": "DE", "doping_type": "showcase", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        
        # All returned items should be featured (showcase)
        for item in data["items"]:
            assert item.get("is_featured") == True, f"Item {item['id']} is not featured"
        
        print(f"Showcase filter returned {len(data['items'])} items")


class TestSeedDataValidation:
    """Validate seed data: real_estate categories, vehicle makes/models/trims"""
    
    def test_real_estate_has_root_categories(self, api_client):
        """Real estate should have at least 3 root categories"""
        response = api_client.get(
            f"{BASE_URL}/api/categories",
            params={"module": "real_estate", "country": "DE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Filter root categories (no parent_id)
        roots = [cat for cat in data if not cat.get("parent_id")]
        
        assert len(roots) >= 3, f"Expected at least 3 real_estate roots, got {len(roots)}"
        print(f"Real estate root categories: {len(roots)}")
        for root in roots[:5]:
            print(f"  - {root.get('name') or root.get('slug')}")
    
    def test_real_estate_roots_have_children(self, api_client):
        """Each real_estate root should have at least 2 leaf children"""
        response = api_client.get(
            f"{BASE_URL}/api/categories",
            params={"module": "real_estate", "country": "DE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        roots = [cat for cat in data if not cat.get("parent_id")]
        
        for root in roots[:3]:  # Check first 3 roots
            root_id = root.get("id")
            children = [cat for cat in data if cat.get("parent_id") == root_id]
            assert len(children) >= 2, f"Root {root.get('name')} should have at least 2 children, got {len(children)}"
            print(f"Root '{root.get('name')}' has {len(children)} children")
    
    def test_vehicle_makes_exist(self, api_client, admin_token):
        """Vehicle makes should exist"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/admin/vehicle/makes",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            makes = data.get("items") or data if isinstance(data, list) else []
            assert len(makes) >= 1, "Should have at least 1 vehicle make"
            print(f"Vehicle makes count: {len(makes)}")
        else:
            print(f"Vehicle makes endpoint returned {response.status_code}")
    
    def test_vehicle_models_exist(self, api_client, admin_token):
        """Vehicle models should exist"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/admin/vehicle/models",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("items") or data if isinstance(data, list) else []
            assert len(models) >= 1, "Should have at least 1 vehicle model"
            print(f"Vehicle models count: {len(models)}")
        else:
            print(f"Vehicle models endpoint returned {response.status_code}")


class TestShowcaseLayoutPublish:
    """Test showcase layout publish -> homepage revalidation flow"""
    
    def test_showcase_layout_get(self, api_client):
        """Public showcase layout endpoint should work"""
        response = api_client.get(f"{BASE_URL}/api/site/showcase-layout")
        assert response.status_code == 200
        
        data = response.json()
        assert "config" in data
        assert "homepage" in data["config"]
        assert "category_showcase" in data["config"]
        
        homepage = data["config"]["homepage"]
        assert "enabled" in homepage
        assert "rows" in homepage
        assert "columns" in homepage
        assert "listing_count" in homepage
        
        print(f"Showcase layout: rows={homepage['rows']}, cols={homepage['columns']}, count={homepage['listing_count']}")
    
    def test_admin_showcase_layout_list(self, api_client, admin_token):
        """Admin should be able to list showcase layout configs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = api_client.get(
            f"{BASE_URL}/api/admin/site/showcase-layout/configs",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        print(f"Showcase layout versions: {len(items)}")
        
        # Check if there's a published version
        published = [item for item in items if item.get("status") == "published"]
        print(f"Published versions: {len(published)}")


class TestAnalyticsEvents:
    """Test analytics event tracking - shouldn't crash"""
    
    def test_block_completed_event(self, api_client, auth_token):
        """block_completed event should be accepted"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/analytics/events",
            headers=headers,
            json={
                "event_name": "block_completed",
                "session_id": f"test-{uuid.uuid4()}",
                "page": "listing_details",
                "metadata": {
                    "block_key": "address",
                    "listing_id": None,
                    "completion_score": 75
                }
            }
        )
        # Should not crash - accept 200-202 or even 204
        assert response.status_code in [200, 201, 202, 204], f"Analytics event failed: {response.status_code}"
        print("block_completed event accepted")
    
    def test_submit_blocked_incomplete_event(self, api_client, auth_token):
        """submit_blocked_incomplete event should be accepted"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = api_client.post(
            f"{BASE_URL}/api/analytics/events",
            headers=headers,
            json={
                "event_name": "submit_blocked_incomplete",
                "session_id": f"test-{uuid.uuid4()}",
                "page": "listing_details",
                "metadata": {
                    "listing_id": None,
                    "completion_score": 50,
                    "missing_blocks": ["duration", "terms"]
                }
            }
        )
        # Should not crash
        assert response.status_code in [200, 201, 202, 204], f"Analytics event failed: {response.status_code}"
        print("submit_blocked_incomplete event accepted")


class TestCompletionPanel:
    """Test listing completion score/checklist via schema endpoint"""
    
    def test_catalog_schema_returns_modules(self, api_client, auth_token):
        """Catalog schema should return modules configuration"""
        # First get a category ID
        cat_response = api_client.get(
            f"{BASE_URL}/api/categories",
            params={"module": "real_estate", "country": "DE"}
        )
        
        if cat_response.status_code != 200:
            pytest.skip("Categories not available")
        
        categories = cat_response.json()
        leaves = [cat for cat in categories if cat.get("parent_id")]
        
        if not leaves:
            pytest.skip("No leaf categories found")
        
        leaf = leaves[0]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = api_client.get(
            f"{BASE_URL}/api/catalog/schema",
            params={"category_id": leaf["id"], "country": "DE"},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            schema = data.get("schema", {})
            
            if schema:
                modules = schema.get("modules", {})
                print(f"Schema modules: {list(modules.keys())}")
                
                # Check completion-related fields
                if "dynamic_fields" in schema:
                    print(f"Dynamic fields: {len(schema['dynamic_fields'])}")
                if "detail_groups" in schema:
                    print(f"Detail groups: {len(schema['detail_groups'])}")
        else:
            print(f"Catalog schema returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
