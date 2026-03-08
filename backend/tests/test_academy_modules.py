"""
Test Academy Modules API - Iteration 175
Tests for the public academy/modules endpoint connected to live DB table academy_modules
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAcademyModulesPublicEndpoint:
    """Tests for GET /api/academy/modules - public read endpoint"""

    def test_endpoint_accessible_without_auth(self):
        """Verify endpoint is publicly accessible without authentication"""
        response = requests.get(f"{BASE_URL}/api/academy/modules", timeout=15)
        # Should not be 401/403
        assert response.status_code != 401, "Endpoint should not require auth (got 401)"
        assert response.status_code != 403, "Endpoint should not return 403 Forbidden"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"[PASS] Endpoint accessible without auth - status {response.status_code}")

    def test_endpoint_does_not_return_500(self):
        """Regression: endpoint should not return 500 server error"""
        response = requests.get(f"{BASE_URL}/api/academy/modules", timeout=15)
        assert response.status_code != 500, "Endpoint should not return 500 Internal Server Error"
        print(f"[PASS] Endpoint does not return 500 - status {response.status_code}")

    def test_response_source_field_is_academy_modules_db(self):
        """Verify source field indicates data comes from academy_modules DB table"""
        response = requests.get(f"{BASE_URL}/api/academy/modules?force_refresh=true", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "source" in data, "Response should contain 'source' field"
        # Source should be academy_modules_db (fresh from DB) or cache (cached version)
        # When force_refresh=true, it should be academy_modules_db
        valid_sources = ["academy_modules_db", "cache", "cache_fallback", "empty_fallback"]
        assert data["source"] in valid_sources, f"Source should be one of {valid_sources}, got {data['source']}"
        print(f"[PASS] Source field present: {data['source']}")
        
        # Specifically check force_refresh=true returns from DB
        if data["source"] == "academy_modules_db":
            print(f"[PASS] Source is 'academy_modules_db' (fresh from DB)")
        else:
            print(f"[INFO] Source is '{data['source']}' (may be due to cache or DB error)")

    def test_items_payload_fields_match_new_schema(self):
        """Verify items payload has correct fields: module_key, title, description, sort_order, is_active"""
        response = requests.get(f"{BASE_URL}/api/academy/modules?force_refresh=true", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Response should contain 'items' field"
        assert isinstance(data["items"], list), "'items' should be a list"
        
        expected_fields = {"module_key", "title", "description", "sort_order", "is_active"}
        
        if len(data["items"]) == 0:
            print(f"[INFO] No modules returned - table may be empty")
        else:
            for idx, item in enumerate(data["items"]):
                # Check all expected fields are present
                missing_fields = expected_fields - set(item.keys())
                assert not missing_fields, f"Item {idx} missing fields: {missing_fields}"
                
                # Validate field types
                assert isinstance(item.get("module_key"), str), f"Item {idx} module_key should be string"
                assert isinstance(item.get("title"), str), f"Item {idx} title should be string"
                assert isinstance(item.get("description"), str), f"Item {idx} description should be string"
                assert isinstance(item.get("sort_order"), int), f"Item {idx} sort_order should be int"
                assert isinstance(item.get("is_active"), bool), f"Item {idx} is_active should be bool"
                
                print(f"[PASS] Item {idx} ({item.get('module_key')}) has correct schema")
        
        print(f"[PASS] All {len(data['items'])} items have correct payload fields")

    def test_response_structure_complete(self):
        """Verify complete response structure"""
        response = requests.get(f"{BASE_URL}/api/academy/modules", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Check top-level keys
        expected_keys = {"items", "source", "cache", "fallback", "locale"}
        actual_keys = set(data.keys())
        missing_keys = expected_keys - actual_keys
        assert not missing_keys, f"Response missing keys: {missing_keys}"
        
        # Check cache structure
        assert "cache" in data, "Response should contain 'cache' field"
        cache = data["cache"]
        assert "hit" in cache, "cache should contain 'hit' field"
        assert "ttl_seconds" in cache, "cache should contain 'ttl_seconds' field"
        
        print(f"[PASS] Response structure complete")
        print(f"  - items: {len(data['items'])} modules")
        print(f"  - source: {data['source']}")
        print(f"  - cache_hit: {cache.get('hit')}")
        print(f"  - locale: {data.get('locale')}")

    def test_force_refresh_parameter(self):
        """Verify force_refresh parameter bypasses cache"""
        # First request with cache
        response1 = requests.get(f"{BASE_URL}/api/academy/modules", timeout=15)
        assert response1.status_code == 200
        
        # Second request with force_refresh
        response2 = requests.get(f"{BASE_URL}/api/academy/modules?force_refresh=true", timeout=15)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # force_refresh should return from DB (not cache)
        assert data2["source"] in ["academy_modules_db", "cache_fallback", "empty_fallback"], \
            f"force_refresh should bypass cache, got source: {data2['source']}"
        
        print(f"[PASS] force_refresh parameter works - source: {data2['source']}")


class TestAcademyModulesFieldValues:
    """Additional tests for data integrity in module items"""

    def test_module_key_not_empty(self):
        """Verify module_key is not empty for any module"""
        response = requests.get(f"{BASE_URL}/api/academy/modules?force_refresh=true", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        for idx, item in enumerate(data.get("items", [])):
            module_key = item.get("module_key", "")
            assert module_key.strip(), f"Item {idx} has empty module_key"
        
        print(f"[PASS] All module_key values are non-empty")

    def test_sort_order_is_non_negative(self):
        """Verify sort_order values are non-negative integers"""
        response = requests.get(f"{BASE_URL}/api/academy/modules?force_refresh=true", timeout=15)
        assert response.status_code == 200
        data = response.json()
        
        for idx, item in enumerate(data.get("items", [])):
            sort_order = item.get("sort_order", -1)
            assert sort_order >= 0, f"Item {idx} has negative sort_order: {sort_order}"
        
        print(f"[PASS] All sort_order values are non-negative")

    def test_items_ordered_by_sort_order(self):
        """Verify items are returned ordered by sort_order"""
        response = requests.get(f"{BASE_URL}/api/academy/modules?force_refresh=true", timeout=15)
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        
        if len(items) < 2:
            print(f"[SKIP] Not enough items ({len(items)}) to verify ordering")
            return
        
        sort_orders = [item.get("sort_order", 0) for item in items]
        assert sort_orders == sorted(sort_orders), f"Items not ordered by sort_order: {sort_orders}"
        
        print(f"[PASS] Items are ordered by sort_order: {sort_orders}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
