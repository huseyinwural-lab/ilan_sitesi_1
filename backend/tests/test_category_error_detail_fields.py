"""
Test Category Error Detail Fields (P0 Hotfix Verification)

Tests for category CRUD error handling improvements:
- PATCH /api/admin/categories/{id}: slug unchanged -> 200 (no false 409)
- Duplicate slug: 409 with detail containing field_name=slug + conflict
- Invalid parent_id: 400 with field_name=parent_id
- Sort order conflict: 409 with field_name=sort_order + conflict details
- Frontend parseApiError: 'Alan: <field>' format messages

Admin credentials: admin@platform.com / Admin123!
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestCategoryErrorDetailFields:
    """Test category API error detail payload with field_name and conflict."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Store test category ids for cleanup
        self.test_category_ids = []
        yield
        
        # Cleanup test categories
        for cat_id in self.test_category_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/categories/{cat_id}")
            except Exception:
                pass

    def _create_test_category(self, name_suffix: str, slug_suffix: str, **kwargs) -> dict:
        """Create a test category and track for cleanup."""
        timestamp = datetime.now().strftime("%H%M%S%f")[:10]
        payload = {
            "name": f"TEST_{name_suffix}_{timestamp}",
            "slug": f"test-{slug_suffix}-{timestamp}",
            "module": kwargs.get("module", "vehicle"),
            "country_code": kwargs.get("country_code", "DE"),
            "active_flag": kwargs.get("active_flag", True),
            "sort_order": kwargs.get("sort_order", 999),
            "parent_id": kwargs.get("parent_id", None),
        }
        response = self.session.post(f"{BASE_URL}/api/admin/categories", json=payload)
        if response.status_code in (200, 201):
            data = response.json()
            category = data.get("category", data)
            self.test_category_ids.append(category["id"])
            return category
        return None

    def test_patch_same_slug_returns_200(self):
        """
        Test: PATCH with unchanged slug should return 200, not 409.
        This was the original bug - false positive slug conflict.
        """
        # Create a test category
        category = self._create_test_category("same_slug_test", "same-slug")
        assert category is not None, "Failed to create test category"
        
        category_id = category["id"]
        original_slug = category.get("slug")
        if isinstance(original_slug, dict):
            original_slug = original_slug.get("tr") or original_slug.get("en") or list(original_slug.values())[0]
        
        # PATCH with same slug - should return 200
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            json={
                "slug": original_slug,
                "name": f"Updated Name {datetime.now().timestamp()}"
            }
        )
        
        assert patch_response.status_code == 200, f"Same slug PATCH should return 200, got {patch_response.status_code}: {patch_response.text}"
        print("TEST PASS: PATCH with same slug returns 200 (no false 409)")

    def test_duplicate_slug_returns_409_with_field_name(self):
        """
        Test: PATCH with slug belonging to another category -> 409 with field_name=slug.
        """
        # Create two categories
        cat1 = self._create_test_category("dup_slug_1", "dupslug-first")
        cat2 = self._create_test_category("dup_slug_2", "dupslug-second")
        
        assert cat1 is not None, "Failed to create first test category"
        assert cat2 is not None, "Failed to create second test category"
        
        # Get cat1's slug
        cat1_slug = cat1.get("slug")
        if isinstance(cat1_slug, dict):
            cat1_slug = cat1_slug.get("tr") or cat1_slug.get("en") or list(cat1_slug.values())[0]
        
        # Try to update cat2 with cat1's slug - should return 409
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{cat2['id']}",
            json={"slug": cat1_slug}
        )
        
        assert patch_response.status_code == 409, f"Duplicate slug should return 409, got {patch_response.status_code}"
        
        error_data = patch_response.json()
        detail = error_data.get("detail", {})
        
        # Verify detail contains field_name
        assert isinstance(detail, dict), "detail should be an object"
        assert detail.get("field_name") == "slug", f"Expected field_name='slug', got '{detail.get('field_name')}'"
        assert detail.get("error_code") == "CATEGORY_SLUG_CONFLICT", f"Expected error_code='CATEGORY_SLUG_CONFLICT', got '{detail.get('error_code')}'"
        
        # Verify conflict info
        conflict = detail.get("conflict")
        assert conflict is not None, "detail.conflict should be present"
        assert conflict.get("slug") == cat1_slug, f"conflict.slug should match: expected '{cat1_slug}', got '{conflict.get('slug')}'"
        
        print(f"TEST PASS: Duplicate slug returns 409 with field_name=slug and conflict={{slug: '{cat1_slug}'}}")

    def test_invalid_parent_id_returns_400_with_field_name(self):
        """
        Test: PATCH with invalid parent_id format -> 400 with field_name=parent_id.
        """
        category = self._create_test_category("invalid_parent_test", "invalid-parent")
        assert category is not None, "Failed to create test category"
        
        # Try to update with invalid UUID
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{category['id']}",
            json={"parent_id": "not-a-valid-uuid"}
        )
        
        assert patch_response.status_code == 400, f"Invalid parent_id should return 400, got {patch_response.status_code}"
        
        error_data = patch_response.json()
        detail = error_data.get("detail", {})
        
        # Verify field_name
        assert isinstance(detail, dict), "detail should be an object"
        assert detail.get("field_name") == "parent_id", f"Expected field_name='parent_id', got '{detail.get('field_name')}'"
        assert "PARENT_ID_INVALID" in detail.get("error_code", ""), f"Expected error_code containing 'PARENT_ID_INVALID'"
        
        print(f"TEST PASS: Invalid parent_id returns 400 with field_name=parent_id")

    def test_nonexistent_parent_id_returns_400_with_field_name(self):
        """
        Test: PATCH with non-existent parent_id -> 400 with field_name=parent_id.
        """
        category = self._create_test_category("nonexist_parent_test", "nonexist-parent")
        assert category is not None, "Failed to create test category"
        
        # Try to update with a valid UUID format but non-existent
        fake_uuid = str(uuid.uuid4())
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{category['id']}",
            json={"parent_id": fake_uuid}
        )
        
        assert patch_response.status_code == 400, f"Non-existent parent_id should return 400, got {patch_response.status_code}"
        
        error_data = patch_response.json()
        detail = error_data.get("detail", {})
        
        assert isinstance(detail, dict), "detail should be an object"
        assert detail.get("field_name") == "parent_id", f"Expected field_name='parent_id', got '{detail.get('field_name')}'"
        assert "PARENT_ID_NOT_FOUND" in detail.get("error_code", ""), f"Expected error_code containing 'PARENT_ID_NOT_FOUND'"
        
        print(f"TEST PASS: Non-existent parent_id returns 400 with field_name=parent_id")

    def test_sort_order_conflict_returns_409_with_field_name_and_conflict(self):
        """
        Test: PATCH/POST with duplicate sort_order -> 409 with field_name=sort_order and conflict details.
        """
        # Create first category with specific sort_order
        sort_order_value = 12345
        cat1 = self._create_test_category("sort_conflict_1", "sort-first", sort_order=sort_order_value)
        
        # If cat1 creation fails due to existing sort_order, try a different value
        if cat1 is None:
            sort_order_value = int(datetime.now().timestamp()) % 99999
            cat1 = self._create_test_category("sort_conflict_1", "sort-first", sort_order=sort_order_value)
        
        assert cat1 is not None, "Failed to create first test category"
        
        # Create second category with different sort_order
        cat2 = self._create_test_category("sort_conflict_2", "sort-second", sort_order=sort_order_value + 100)
        assert cat2 is not None, "Failed to create second test category"
        
        # Try to update cat2 with cat1's sort_order - should return 409
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{cat2['id']}",
            json={"sort_order": sort_order_value}
        )
        
        assert patch_response.status_code == 409, f"Sort order conflict should return 409, got {patch_response.status_code}"
        
        error_data = patch_response.json()
        detail = error_data.get("detail", {})
        
        # Verify field_name
        assert isinstance(detail, dict), "detail should be an object"
        assert detail.get("field_name") == "sort_order", f"Expected field_name='sort_order', got '{detail.get('field_name')}'"
        assert detail.get("error_code") == "ORDER_INDEX_ALREADY_USED", f"Expected error_code='ORDER_INDEX_ALREADY_USED'"
        
        # Verify conflict info
        conflict = detail.get("conflict")
        assert conflict is not None, "detail.conflict should be present for sort_order conflict"
        assert conflict.get("sort_order") == sort_order_value, f"conflict.sort_order should be {sort_order_value}"
        assert conflict.get("id") is not None, "conflict.id should be present"
        
        print(f"TEST PASS: Sort order conflict returns 409 with field_name=sort_order and conflict details")

    def test_parent_module_mismatch_returns_409_with_field_name(self):
        """
        Test: PATCH with parent_id from different module -> 409 with field_name=parent_id.
        """
        # Create a vehicle category (to be used as invalid parent)
        vehicle_cat = self._create_test_category("vehicle_parent", "vehicle-parent", module="vehicle")
        
        # Create a real_estate category
        re_cat = self._create_test_category("re_child", "re-child", module="real_estate")
        
        if vehicle_cat is None or re_cat is None:
            pytest.skip("Could not create test categories for parent module mismatch test")
        
        # Try to set vehicle category as parent of real_estate category
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{re_cat['id']}",
            json={"parent_id": vehicle_cat["id"]}
        )
        
        assert patch_response.status_code == 409, f"Parent module mismatch should return 409, got {patch_response.status_code}"
        
        error_data = patch_response.json()
        detail = error_data.get("detail", {})
        
        assert isinstance(detail, dict), "detail should be an object"
        assert detail.get("field_name") == "parent_id", f"Expected field_name='parent_id', got '{detail.get('field_name')}'"
        assert "PARENT_MODULE_MISMATCH" in detail.get("error_code", ""), f"Expected error_code containing 'PARENT_MODULE_MISMATCH'"
        
        # Verify conflict info shows module mismatch details
        conflict = detail.get("conflict")
        assert conflict is not None, "conflict should be present"
        assert "parent_module" in conflict, "conflict should contain parent_module"
        
        print(f"TEST PASS: Parent module mismatch returns 409 with field_name=parent_id and conflict details")


class TestFrontendParseApiErrorFormat:
    """Test that error detail format is compatible with frontend parseApiError."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token."""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        self.test_category_ids = []
        yield
        
        for cat_id in self.test_category_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/categories/{cat_id}")
            except Exception:
                pass

    def _create_test_category(self, name_suffix: str, slug_suffix: str, **kwargs) -> dict:
        timestamp = datetime.now().strftime("%H%M%S%f")[:10]
        payload = {
            "name": f"TEST_{name_suffix}_{timestamp}",
            "slug": f"test-{slug_suffix}-{timestamp}",
            "module": kwargs.get("module", "vehicle"),
            "country_code": kwargs.get("country_code", "DE"),
            "active_flag": kwargs.get("active_flag", True),
            "sort_order": kwargs.get("sort_order", 888),
            "parent_id": kwargs.get("parent_id", None),
        }
        response = self.session.post(f"{BASE_URL}/api/admin/categories", json=payload)
        if response.status_code in (200, 201):
            data = response.json()
            category = data.get("category", data)
            self.test_category_ids.append(category["id"])
            return category
        return None

    def test_error_detail_structure_for_frontend(self):
        """
        Verify error detail structure is compatible with frontend parseApiError function.
        Frontend expects: detail.field_name, detail.message, detail.conflict
        Frontend formats: 'Alan: <field_name> • <message>'
        """
        # Create two categories with same slug to trigger conflict
        cat1 = self._create_test_category("frontend_test_1", "frontend-slug")
        cat2 = self._create_test_category("frontend_test_2", "frontend-second")
        
        if cat1 is None or cat2 is None:
            pytest.skip("Could not create test categories")
        
        cat1_slug = cat1.get("slug")
        if isinstance(cat1_slug, dict):
            cat1_slug = cat1_slug.get("tr") or list(cat1_slug.values())[0]
        
        # Trigger slug conflict
        patch_response = self.session.patch(
            f"{BASE_URL}/api/admin/categories/{cat2['id']}",
            json={"slug": cat1_slug}
        )
        
        assert patch_response.status_code == 409
        
        error_data = patch_response.json()
        detail = error_data.get("detail", {})
        
        # Verify structure matches frontend expectations
        assert isinstance(detail, dict), "detail must be an object for parseApiError"
        
        # These fields are used by parseApiError in AdminCategories.js
        field_name = detail.get("field_name", "")
        message = detail.get("message", "")
        conflict = detail.get("conflict")
        error_code = detail.get("error_code", "")
        
        assert field_name, "field_name should be present"
        assert message, "message should be present"
        
        # Simulate frontend parseApiError logic
        human_message = f"Alan: {field_name} • {message}" if field_name else message
        
        if field_name == "slug" and conflict and conflict.get("slug"):
            human_message = f"{human_message} (Çakışan slug: {conflict['slug']})"
        
        print(f"Frontend would display: '{human_message}'")
        print(f"TEST PASS: Error detail structure compatible with frontend parseApiError")
        
        # Verify the complete structure
        assert error_code == "CATEGORY_SLUG_CONFLICT"
        assert field_name == "slug"
        assert conflict is not None
        assert conflict.get("slug") == cat1_slug


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
