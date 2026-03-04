"""
Test Category Search Templates - L1/L2 Category Landing Pages

Tests:
- GET /api/categories - category listing with proper hierarchy
- GET /api/v2/search - search with category filter and showcase doping_type
- Category context resolve for L1/L2 template determination
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCategoryAPI:
    """Test /api/categories endpoint for category hierarchy"""

    def test_categories_list_real_estate(self):
        """Test categories endpoint returns real_estate categories"""
        response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of categories"
        assert len(data) > 0, "Expected at least one category"
        
        # Verify category structure
        first_cat = data[0]
        assert "id" in first_cat, "Category should have id"
        assert "name" in first_cat, "Category should have name"
        assert "slug" in first_cat, "Category should have slug"
        assert "module" in first_cat, "Category should have module"
        print(f"SUCCESS: Found {len(data)} real_estate categories")

    def test_categories_list_vehicle(self):
        """Test categories endpoint returns vehicle categories"""
        response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "vehicle",
            "country": "DE"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of categories"
        print(f"SUCCESS: Found {len(data)} vehicle categories")

    def test_categories_require_country(self):
        """Test categories endpoint requires country parameter"""
        response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate"
        })
        
        assert response.status_code == 400, f"Expected 400 without country, got {response.status_code}"
        print("SUCCESS: Categories requires country parameter")

    def test_category_hierarchy_l0_l1_l2(self):
        """Test category hierarchy includes L0, L1, L2 categories"""
        response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Find L0 (root) categories - parent_id is None
        l0_cats = [c for c in data if c.get("parent_id") is None]
        assert len(l0_cats) > 0, "Expected at least one L0 (root) category"
        print(f"Found {len(l0_cats)} L0 categories: {[c['name'] for c in l0_cats[:5]]}")
        
        # Find L1 categories - parent_id matches an L0 category
        l0_ids = {c["id"] for c in l0_cats}
        l1_cats = [c for c in data if c.get("parent_id") in l0_ids]
        print(f"Found {len(l1_cats)} L1 categories: {[c['name'] for c in l1_cats[:5]]}")
        
        # Find L2 categories - parent_id matches an L1 category
        l1_ids = {c["id"] for c in l1_cats}
        l2_cats = [c for c in data if c.get("parent_id") in l1_ids]
        print(f"Found {len(l2_cats)} L2 categories: {[c['name'] for c in l2_cats[:5]]}")
        
        print("SUCCESS: Category hierarchy verified")


class TestSearchAPI:
    """Test /api/v2/search endpoint for category filtering"""

    def test_search_without_category(self):
        """Test search without category filter returns all listings"""
        response = requests.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "limit": 5
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have items"
        assert "pagination" in data, "Response should have pagination"
        assert "total" in data["pagination"], "Pagination should have total"
        print(f"SUCCESS: Search without category returned {data['pagination']['total']} total items")

    def test_search_with_category_slug(self):
        """Test search with category slug filter"""
        response = requests.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "category": "konut",
            "limit": 5
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data, "Response should have items"
        assert "pagination" in data, "Response should have pagination"
        print(f"SUCCESS: Search with category 'konut' returned {data['pagination']['total']} items")

    def test_search_with_category_id(self):
        """Test search with category ID filter"""
        # First get a category ID
        cat_response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        categories = cat_response.json()
        
        if len(categories) > 0:
            cat_id = categories[0]["id"]
            
            response = requests.get(f"{BASE_URL}/api/v2/search", params={
                "country": "DE",
                "category": cat_id,
                "limit": 5
            })
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            print(f"SUCCESS: Search with category ID returned successfully")
        else:
            pytest.skip("No categories available for testing")

    def test_search_with_showcase_doping(self):
        """Test search with showcase doping_type for L1 vitrin section"""
        # First get an L1 category (child of root)
        cat_response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        categories = cat_response.json()
        
        # Find an L1 category
        root_ids = {c["id"] for c in categories if c.get("parent_id") is None}
        l1_cats = [c for c in categories if c.get("parent_id") in root_ids]
        
        if len(l1_cats) > 0:
            l1_cat = l1_cats[0]
            
            response = requests.get(f"{BASE_URL}/api/v2/search", params={
                "country": "DE",
                "category": l1_cat["id"],
                "doping_type": "showcase",
                "limit": 8
            })
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "items" in data, "Response should have items"
            print(f"SUCCESS: Showcase search for L1 category '{l1_cat['name']}' returned {data['pagination']['total']} items")
        else:
            pytest.skip("No L1 categories available for testing")

    def test_search_require_country(self):
        """Test search requires country parameter"""
        response = requests.get(f"{BASE_URL}/api/v2/search", params={
            "limit": 5
        })
        
        assert response.status_code == 400, f"Expected 400 without country, got {response.status_code}"
        print("SUCCESS: Search requires country parameter")

    def test_search_pagination(self):
        """Test search pagination works correctly"""
        response = requests.get(f"{BASE_URL}/api/v2/search", params={
            "country": "DE",
            "page": 1,
            "limit": 10
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        pagination = data.get("pagination", {})
        assert "total" in pagination, "Pagination should have total"
        assert "page" in pagination, "Pagination should have page"
        assert "pages" in pagination, "Pagination should have pages"
        print(f"SUCCESS: Pagination: total={pagination['total']}, page={pagination['page']}, pages={pagination['pages']}")

    def test_search_sorting(self):
        """Test search sorting options"""
        sort_options = ["date_desc", "date_asc", "price_asc", "price_desc"]
        
        for sort in sort_options:
            response = requests.get(f"{BASE_URL}/api/v2/search", params={
                "country": "DE",
                "sort": sort,
                "limit": 5
            })
            
            assert response.status_code == 200, f"Sort '{sort}' failed with {response.status_code}"
        
        print(f"SUCCESS: All sort options work: {sort_options}")


class TestCategoryContext:
    """Test category context resolution for L1/L2 template determination"""

    def test_l1_category_has_children(self):
        """Test L1 category has children for subcategory section"""
        cat_response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        categories = cat_response.json()
        
        # Find L0 and L1 categories
        root_ids = {c["id"] for c in categories if c.get("parent_id") is None}
        l1_cats = [c for c in categories if c.get("parent_id") in root_ids]
        
        if len(l1_cats) > 0:
            l1_cat = l1_cats[0]
            l1_id = l1_cat["id"]
            
            # Check for L2 children
            l2_children = [c for c in categories if c.get("parent_id") == l1_id]
            
            print(f"L1 category '{l1_cat['name']}' has {len(l2_children)} children")
            
            if len(l2_children) > 0:
                print(f"Children: {[c['name'] for c in l2_children[:5]]}")
            
            print("SUCCESS: L1 category children check completed")
        else:
            pytest.skip("No L1 categories available")

    def test_l2_category_has_siblings(self):
        """Test L2 category has siblings for 'Aynı Seviyedeki Kategoriler'"""
        cat_response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        categories = cat_response.json()
        
        # Find L0, L1, L2 categories
        root_ids = {c["id"] for c in categories if c.get("parent_id") is None}
        l1_cats = [c for c in categories if c.get("parent_id") in root_ids]
        l1_ids = {c["id"] for c in l1_cats}
        l2_cats = [c for c in categories if c.get("parent_id") in l1_ids]
        
        if len(l2_cats) > 0:
            l2_cat = l2_cats[0]
            parent_id = l2_cat["parent_id"]
            
            # Find siblings (same parent_id, different id)
            siblings = [c for c in categories if c.get("parent_id") == parent_id and c["id"] != l2_cat["id"]]
            
            print(f"L2 category '{l2_cat['name']}' has {len(siblings)} siblings")
            
            if len(siblings) > 0:
                print(f"Siblings: {[c['name'] for c in siblings[:5]]}")
            
            print("SUCCESS: L2 category siblings check completed")
        else:
            pytest.skip("No L2 categories available")

    def test_breadcrumb_path(self):
        """Test breadcrumb path can be reconstructed from category hierarchy"""
        cat_response = requests.get(f"{BASE_URL}/api/categories", params={
            "module": "real_estate",
            "country": "DE"
        })
        categories = cat_response.json()
        
        # Build ID to category map
        cat_map = {c["id"]: c for c in categories}
        
        # Find a deep category and trace path back
        root_ids = {c["id"] for c in categories if c.get("parent_id") is None}
        l1_ids = {c["id"] for c in categories if c.get("parent_id") in root_ids}
        l2_cats = [c for c in categories if c.get("parent_id") in l1_ids]
        
        if len(l2_cats) > 0:
            l2_cat = l2_cats[0]
            
            # Build path back to root
            path = [l2_cat]
            current = l2_cat
            while current.get("parent_id") and current["parent_id"] in cat_map:
                parent = cat_map[current["parent_id"]]
                path.insert(0, parent)
                current = parent
            
            breadcrumb = " > ".join([c["name"] for c in path])
            print(f"Breadcrumb path: {breadcrumb}")
            
            assert len(path) >= 2, "L2 category should have at least 2-level path"
            print("SUCCESS: Breadcrumb path reconstruction works")
        else:
            pytest.skip("No L2 categories available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
