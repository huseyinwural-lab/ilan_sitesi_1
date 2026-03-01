"""
Test Category Seed Schema - Real Estate Standard Hierarchy
Tests:
1. POST /api/admin/categories/seed/real-estate-standard creates proper hierarchy
2. Idempotent behavior (no duplicates on second call)
3. Category hierarchy: Emlak -> (Konut, Ticari Alan, Arsa) -> (Satılık, Kiralık, Günlük Kiralık) -> (Daire, Müstakil Ev, Köşk & Konak, Bina, Çiftlik Evi)
4. Admin categories endpoint returns proper data
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin auth failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestCategorySeedRealEstateStandard:
    """Test seed endpoint for real estate standard hierarchy"""

    def test_seed_endpoint_first_call(self, auth_headers):
        """Test POST /api/admin/categories/seed/real-estate-standard creates categories"""
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/seed/real-estate-standard?country=DE",
            headers=auth_headers,
        )
        
        assert response.status_code == 200, f"Seed failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("ok") is True
        assert data.get("country") == "DE"
        assert data.get("module") == "real_estate"
        assert "created_count" in data
        assert "reused_count" in data
        assert "items" in data
        
        print(f"Seed response: created={data['created_count']}, reused={data['reused_count']}")

    def test_seed_endpoint_idempotent(self, auth_headers):
        """Test seed endpoint is idempotent (second call creates no duplicates)"""
        # Second call to seed
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/seed/real-estate-standard?country=DE",
            headers=auth_headers,
        )
        
        assert response.status_code == 200, f"Seed failed: {response.text}"
        data = response.json()
        
        assert data.get("ok") is True
        # On idempotent call, created_count should be 0
        created_count = data.get("created_count", -1)
        reused_count = data.get("reused_count", -1)
        
        print(f"Idempotent check: created={created_count}, reused={reused_count}")
        
        # All should be reused if already created
        assert created_count == 0, f"Expected 0 created on idempotent call, got {created_count}"
        assert reused_count > 0, f"Expected reused > 0, got {reused_count}"

    def test_category_hierarchy_structure(self, auth_headers):
        """Verify the hierarchy: Emlak -> (Konut, Ticari Alan, Arsa) -> (Satılık, Kiralık, Günlük Kiralık) -> (Daire, ...)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE&module=real_estate",
            headers=auth_headers,
        )
        
        assert response.status_code == 200, f"Categories fetch failed: {response.text}"
        data = response.json()
        items = data.get("items", [])
        
        # Build parent-child map
        by_id = {item["id"]: item for item in items}
        by_parent = {}
        for item in items:
            parent_key = item.get("parent_id") or "__root__"
            if parent_key not in by_parent:
                by_parent[parent_key] = []
            by_parent[parent_key].append(item)
        
        # Find L1: Emlak (root category)
        roots = by_parent.get("__root__", [])
        emlak_root = None
        for root in roots:
            name = root.get("name", "")
            if "emlak" in name.lower():
                emlak_root = root
                break
        
        assert emlak_root is not None, f"Emlak root not found. Roots: {[r['name'] for r in roots]}"
        print(f"L1 found: {emlak_root['name']} (id={emlak_root['id']})")
        
        # Find L2: Konut, Ticari Alan, Arsa
        l2_items = by_parent.get(emlak_root["id"], [])
        l2_names = [item.get("name", "") for item in l2_items]
        print(f"L2 items: {l2_names}")
        
        expected_l2 = ["Konut", "Ticari Alan", "Arsa"]
        for expected_name in expected_l2:
            found = any(expected_name.lower() in name.lower() for name in l2_names)
            assert found, f"L2 category '{expected_name}' not found. Available: {l2_names}"
        
        # Pick Konut to check L3
        konut_item = next((item for item in l2_items if "konut" in item.get("name", "").lower()), None)
        if konut_item:
            l3_items = by_parent.get(konut_item["id"], [])
            l3_names = [item.get("name", "") for item in l3_items]
            print(f"L3 items under Konut: {l3_names}")
            
            expected_l3 = ["Satılık", "Kiralık", "Günlük Kiralık"]
            for expected_name in expected_l3:
                found = any(expected_name.lower() in name.lower() for name in l3_names)
                assert found, f"L3 category '{expected_name}' not found under Konut. Available: {l3_names}"
            
            # Pick Satılık to check L4
            satilik_item = next((item for item in l3_items if "satılık" in item.get("name", "").lower()), None)
            if satilik_item:
                l4_items = by_parent.get(satilik_item["id"], [])
                l4_names = [item.get("name", "") for item in l4_items]
                print(f"L4 items under Satılık: {l4_names}")
                
                expected_l4 = ["Daire", "Müstakil Ev", "Köşk & Konak", "Bina", "Çiftlik Evi"]
                for expected_name in expected_l4:
                    found = any(expected_name.lower() in name.lower() for name in l4_names)
                    assert found, f"L4 category '{expected_name}' not found under Satılık. Available: {l4_names}"


class TestAdminCategoriesUI:
    """Test admin categories endpoint for UI consumption"""

    def test_admin_categories_list(self, auth_headers):
        """Test GET /api/admin/categories returns correct data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE&module=real_estate",
            headers=auth_headers,
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        items = data.get("items", [])
        
        assert len(items) > 0, "No categories returned"
        
        # Count root vs children
        root_items = [item for item in items if not item.get("parent_id")]
        child_items = [item for item in items if item.get("parent_id")]
        
        print(f"Total: {len(items)}, Roots: {len(root_items)}, Children: {len(child_items)}")
        
        # Verify item structure
        for item in items[:3]:
            assert "id" in item
            assert "name" in item
            assert "module" in item
            assert item.get("module") == "real_estate"


class TestPublicCategoriesForHomePage:
    """Test public category endpoints for home page display"""

    def test_public_categories_endpoint(self):
        """Test GET /api/categories?module=real_estate returns data for homepage"""
        response = requests.get(
            f"{BASE_URL}/api/categories?module=real_estate&country=DE",
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should return array
        categories = data if isinstance(data, list) else data.get("items", [])
        
        print(f"Public categories returned: {len(categories)}")
        
        if len(categories) > 0:
            # Check structure
            first = categories[0]
            assert "id" in first
            assert "name" in first or "translations" in first
            
            # Check for listing_count field
            # This may be optional but useful for UI
            print(f"Sample category keys: {list(first.keys())[:10]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
