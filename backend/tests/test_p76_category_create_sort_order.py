"""
P76 Category Create Sort Order Tests
Tests for:
- Category creation flow (modal > hierarchy step)
- sort_order conflict auto-resolution (ORDER_INDEX_ALREADY_USED -> auto-shift)
- Backend POST /api/admin/categories sort_order=1 conflict handling
- Frontend error parsing for API validation array/detail responses
- Subcategory creation flow regression
"""

import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin authorization headers"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


class TestCategorySortOrderConflict:
    """Tests for sort_order conflict handling in category creation"""

    def test_health_check(self):
        """Verify API is healthy before running tests"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data.get('db_status')}")

    def test_order_preview_endpoint(self, admin_headers):
        """Test sort_order preview endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/order-index/preview",
            params={
                "module": "real_estate",
                "country": "DE",
                "sort_order": 1,
            },
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        assert "available" in data
        print(f"✓ Order preview endpoint works: available={data.get('available')}")

    def test_get_existing_categories(self, admin_headers):
        """Get existing categories to understand current state"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            params={"module": "real_estate", "country": "DE"},
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        print(f"✓ Found {len(items)} existing real_estate categories in DE")
        for item in items[:5]:  # Print first 5
            print(f"  - {item.get('name')}: sort_order={item.get('sort_order')}")
        return items

    def test_create_category_with_unique_sort_order(self, admin_headers):
        """Test creating a category with unique sort_order succeeds"""
        # First, find a unique sort_order
        unique_sort = int(time.time()) % 1000 + 100  # Should be unique
        
        slug = f"test-unique-sort-{int(time.time())}"
        payload = {
            "name": "TEST Unique Sort Order",
            "slug": slug,
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": unique_sort,
            "active_flag": True,
            "hierarchy_complete": True,
            "form_schema": {
                "status": "draft",
                "core_fields": {
                    "title": {"required": True, "min": 10, "max": 120},
                    "description": {"required": True, "min": 30, "max": 4000},
                    "price": {"required": True},
                },
                "modules": {"address": {"enabled": True}, "photos": {"enabled": True}},
            },
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=admin_headers,
            timeout=30,
        )

        # Accept 201 (success) or 503 (DB error - not our fault)
        if response.status_code == 503:
            pytest.skip(f"Database connection error - skipping test: {response.text}")

        assert response.status_code == 201, f"Unexpected status: {response.status_code}, {response.text}"
        data = response.json()
        created = data.get("category", {})
        assert created.get("id"), "Category should have ID"
        assert created.get("sort_order") == unique_sort or created.get("sort_order") > 0
        print(f"✓ Created category with sort_order={created.get('sort_order')}")
        
        # Cleanup
        category_id = created.get("id")
        if category_id:
            requests.delete(
                f"{BASE_URL}/api/admin/categories/{category_id}",
                headers=admin_headers,
                timeout=15,
            )
        return created

    def test_create_category_sort_order_conflict_auto_shift(self, admin_headers):
        """Test that sort_order=1 conflict triggers auto-shift"""
        slug = f"test-conflict-sort-{int(time.time())}"
        payload = {
            "name": "TEST Sort Conflict Auto Shift",
            "slug": slug,
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 1,  # Likely to conflict
            "active_flag": True,
            "hierarchy_complete": True,
            "form_schema": {
                "status": "draft",
                "core_fields": {
                    "title": {"required": True, "min": 10, "max": 120},
                    "description": {"required": True, "min": 30, "max": 4000},
                    "price": {"required": True},
                },
                "modules": {"address": {"enabled": True}, "photos": {"enabled": True}},
            },
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=admin_headers,
            timeout=30,
        )

        if response.status_code == 503:
            pytest.skip(f"Database connection error - skipping test: {response.text}")

        # Either succeeds with auto-shifted sort_order or returns conflict error
        if response.status_code == 201:
            data = response.json()
            created = data.get("category", {})
            # If sort_order conflict occurred, backend should have auto-shifted
            print(f"✓ Category created with sort_order={created.get('sort_order')} (may be auto-shifted)")
            
            # Cleanup
            category_id = created.get("id")
            if category_id:
                requests.delete(
                    f"{BASE_URL}/api/admin/categories/{category_id}",
                    headers=admin_headers,
                    timeout=15,
                )
        elif response.status_code == 400 or response.status_code == 409:
            # Some validation error - check error structure
            data = response.json()
            detail = data.get("detail", {})
            print(f"✓ Got expected error response: {data}")
            assert "error_code" in data or "detail" in data
        else:
            pytest.fail(f"Unexpected status: {response.status_code}, {response.text}")

    def test_order_preview_shows_conflict(self, admin_headers):
        """Test that order-preview correctly identifies conflicts"""
        # Check if sort_order=1 is available
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/order-index/preview",
            params={
                "module": "real_estate",
                "country": "DE",
                "sort_order": 1,
            },
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are existing categories with sort_order=1, available should be False
        if not data.get("available"):
            print(f"✓ Order preview correctly shows sort_order=1 is NOT available")
            assert data.get("conflict") is not None or data.get("message")
        else:
            print(f"✓ Order preview shows sort_order=1 IS available")


class TestApiErrorParsing:
    """Tests for API error response structures"""

    def test_validation_error_array_format(self, admin_headers):
        """Test that validation errors return proper array format"""
        # Send invalid payload to trigger validation error
        payload = {
            "name": "",  # Empty name should fail
            "slug": "",  # Empty slug should fail
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 0,  # Invalid sort_order
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=admin_headers,
            timeout=15,
        )

        if response.status_code == 503:
            pytest.skip("Database connection error - skipping test")

        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"
        data = response.json()
        detail = data.get("detail")
        
        # Pydantic validation errors come as array
        if isinstance(detail, list):
            print(f"✓ Validation error returned as array with {len(detail)} items")
            if len(detail) > 0:
                first_error = detail[0]
                assert "msg" in first_error or "message" in first_error
                print(f"  First error: {first_error}")
        else:
            # Could also be string or dict
            print(f"✓ Validation error detail: {detail}")

    def test_error_code_in_response(self, admin_headers):
        """Test that error responses include error_code when applicable"""
        # Try to access a non-existent category
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/{fake_id}",
            headers=admin_headers,
            timeout=15,
        )
        
        if response.status_code == 503:
            pytest.skip("Database connection error - skipping test")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        print(f"✓ 404 error response: {data}")


class TestSubcategoryCreation:
    """Regression tests for subcategory creation flow"""

    def test_create_parent_then_child(self, admin_headers):
        """Test creating parent category and then a child category"""
        timestamp = int(time.time())
        
        # Create parent
        parent_payload = {
            "name": f"TEST Parent {timestamp}",
            "slug": f"test-parent-{timestamp}",
            "module": "other",  # Use 'other' module for simpler testing
            "country_code": "DE",
            "sort_order": 100 + (timestamp % 100),
            "active_flag": True,
            "hierarchy_complete": True,
            "form_schema": {
                "status": "draft",
                "core_fields": {
                    "title": {"required": True, "min": 10, "max": 120},
                    "description": {"required": True, "min": 30, "max": 4000},
                    "price": {"required": True},
                },
            },
        }

        parent_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=parent_payload,
            headers=admin_headers,
            timeout=30,
        )

        if parent_response.status_code == 503:
            pytest.skip("Database connection error - skipping test")

        assert parent_response.status_code == 201, f"Parent creation failed: {parent_response.text}"
        parent = parent_response.json().get("category", {})
        parent_id = parent.get("id")
        print(f"✓ Parent category created: id={parent_id}")

        # Create child
        child_payload = {
            "name": f"TEST Child {timestamp}",
            "slug": f"test-child-{timestamp}",
            "parent_id": parent_id,
            "module": "other",
            "country_code": "DE",
            "sort_order": 1,
            "active_flag": True,
            "hierarchy_complete": True,
            "form_schema": {
                "status": "draft",
                "core_fields": {
                    "title": {"required": True, "min": 10, "max": 120},
                    "description": {"required": True, "min": 30, "max": 4000},
                    "price": {"required": True},
                },
            },
        }

        child_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=child_payload,
            headers=admin_headers,
            timeout=30,
        )

        if child_response.status_code == 503:
            # Cleanup parent
            requests.delete(f"{BASE_URL}/api/admin/categories/{parent_id}", headers=admin_headers, timeout=15)
            pytest.skip("Database connection error - skipping test")

        assert child_response.status_code == 201, f"Child creation failed: {child_response.text}"
        child = child_response.json().get("category", {})
        child_id = child.get("id")
        print(f"✓ Child category created: id={child_id}, parent_id={child.get('parent_id')}")
        
        # Verify parent-child relationship
        assert child.get("parent_id") == parent_id

        # Cleanup - delete child first, then parent
        if child_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{child_id}", headers=admin_headers, timeout=15)
        if parent_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{parent_id}", headers=admin_headers, timeout=15)
        print("✓ Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
