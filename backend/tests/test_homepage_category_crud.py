"""
Iteration 117 - Homepage Redesign and Category CRUD Tests
Tests for:
- Homepage dynamic data endpoints (/api/categories, /api/v2/search, /api/site/home-category-layout)
- Admin category CRUD with icon_svg field
- Backend verification of icon_svg in create/update/list responses
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Module: Test Credentials
TEST_ADMIN_EMAIL = "admin@platform.com"
TEST_ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Auth headers for admin requests"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestHomepagePublicEndpoints:
    """Test public endpoints used by homepage"""

    def test_public_categories_endpoint(self):
        """Test /api/categories returns data with icon_svg field"""
        response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        
        if len(data) > 0:
            # Verify icon_svg field exists in response
            first_item = data[0]
            assert "icon_svg" in first_item, "icon_svg field missing from category response"
            assert "id" in first_item
            assert "name" in first_item
            assert "slug" in first_item

    def test_home_category_layout_endpoint(self):
        """Test /api/site/home-category-layout returns layout config"""
        response = requests.get(f"{BASE_URL}/api/site/home-category-layout?country=DE")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "config" in data, "config field missing"
        
        config = data["config"]
        assert "column_width" in config
        assert "l1_initial_limit" in config
        assert "module_order" in config

    def test_search_endpoint_for_showcase(self):
        """Test /api/v2/search for showcase listings"""
        response = requests.get(
            f"{BASE_URL}/api/v2/search?country=DE&size=4&page=1&doping_type=showcase&sort=date_desc"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "pagination" in data

    def test_search_endpoint_for_recent(self):
        """Test /api/v2/search for recent listings"""
        response = requests.get(
            f"{BASE_URL}/api/v2/search?country=DE&size=4&page=1&sort=date_desc"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        assert "pagination" in data


class TestAdminCategoryCRUD:
    """Test admin category CRUD operations with icon_svg"""
    
    def test_admin_categories_list(self, admin_headers):
        """Test admin categories list returns icon_svg"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers=admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "items" in data
        
        if len(data["items"]) > 0:
            first_item = data["items"][0]
            assert "icon_svg" in first_item, "icon_svg field missing from admin category list"

    def test_create_category_with_icon_svg(self, admin_headers):
        """Test creating category with icon_svg field"""
        svg_content = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10"/></svg>'
        
        payload = {
            "name": "TEST_Icon Category",
            "slug": "test-icon-category-117",
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 9999,
            "active_flag": True,
            "icon_svg": svg_content,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=admin_headers,
            json=payload,
        )
        assert response.status_code == 201 or response.status_code == 200, f"Expected 201/200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "category" in data
        
        category = data["category"]
        assert category["icon_svg"] == svg_content, "icon_svg not saved correctly"
        assert category["name"] == "TEST_Icon Category"
        
        # Store ID for cleanup
        return category["id"]

    def test_update_category_icon_svg(self, admin_headers):
        """Test updating category icon_svg field"""
        # First create a category
        create_payload = {
            "name": "TEST_Update Icon Category",
            "slug": "test-update-icon-117",
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 9998,
            "active_flag": True,
            "icon_svg": '<svg width="24" height="24"><rect/></svg>',
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=admin_headers,
            json=create_payload,
        )
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["category"]["id"]
        
        # Now update with new icon_svg
        new_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><path d="M12 2L22 12L12 22L2 12Z"/></svg>'
        update_payload = {"icon_svg": new_svg}
        
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=admin_headers,
            json=update_payload,
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_category = update_response.json()["category"]
        assert updated_category["icon_svg"] == new_svg, "icon_svg not updated correctly"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/categories/{category_id}", headers=admin_headers)

    def test_icon_svg_validation(self, admin_headers):
        """Test icon_svg validation rejects invalid SVG"""
        # Test with invalid SVG (no closing tag)
        invalid_payload = {
            "name": "TEST_Invalid SVG",
            "slug": "test-invalid-svg-117",
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 9997,
            "active_flag": True,
            "icon_svg": "<script>alert('xss')</script>",  # Should be rejected
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=admin_headers,
            json=invalid_payload,
        )
        # Should reject malicious content
        assert response.status_code == 400, f"Expected 400 for script tag, got {response.status_code}"

    def test_delete_category(self, admin_headers):
        """Test deleting category"""
        # Create a test category
        payload = {
            "name": "TEST_Delete Category",
            "slug": "test-delete-117",
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 9996,
            "active_flag": True,
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=admin_headers,
            json=payload,
        )
        assert create_response.status_code in [200, 201]
        category_id = create_response.json()["category"]["id"]
        
        # Delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=admin_headers,
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"


class TestHomeCategoryLayoutAdmin:
    """Test admin home category layout endpoint"""
    
    def test_get_layout_config(self, admin_headers):
        """Test GET admin home category layout"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/home-category-layout?country=DE",
            headers=admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "config" in data

    def test_save_layout_config(self, admin_headers):
        """Test PUT admin home category layout"""
        config = {
            "column_width": 280,
            "l1_initial_limit": 6,
            "module_order_mode": "manual",
            "module_order": ["real_estate", "vehicle", "other"],
            "listing_module_grid_columns": 4,
            "listing_lx_limit": 8,
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/site/home-category-layout",
            headers=admin_headers,
            json={"config": config, "country_code": "DE"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "config" in data


# Cleanup test data
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_categories(admin_headers, request):
    """Cleanup any TEST_ prefixed categories after tests"""
    def cleanup():
        try:
            response = requests.get(
                f"{BASE_URL}/api/admin/categories?country=DE",
                headers=admin_headers,
            )
            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    if item.get("name", "").startswith("TEST_"):
                        requests.delete(
                            f"{BASE_URL}/api/admin/categories/{item['id']}",
                            headers=admin_headers,
                        )
        except Exception:
            pass
    
    request.addfinalizer(cleanup)
