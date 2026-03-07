"""
Test Category Edit-Save Flow: Slug unchanged 200, Slug conflict 409, Invalid parent_id 400
Iteration 164: Verify backend field-based error messages and frontend retry mechanism
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Admin credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def auth_headers():
    """Get authentication token for admin user."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def test_categories(auth_headers):
    """Create two test categories for conflict testing."""
    categories = []
    timestamp = int(time.time())
    
    # Create first test category
    payload1 = {
        "name": f"Test Cat A {timestamp}",
        "slug": f"test-cat-a-{timestamp}",
        "module": "other",
        "country_code": "DE",
        "sort_order": 9000 + timestamp % 100,
        "active_flag": True
    }
    resp1 = requests.post(f"{BASE_URL}/api/admin/categories", headers=auth_headers, json=payload1)
    assert resp1.status_code == 201, f"Failed to create category 1: {resp1.text}"
    cat1 = resp1.json().get("category")
    categories.append(cat1)
    
    # Create second test category with different slug
    payload2 = {
        "name": f"Test Cat B {timestamp}",
        "slug": f"test-cat-b-{timestamp}",
        "module": "other",
        "country_code": "DE",
        "sort_order": 9100 + timestamp % 100,
        "active_flag": True
    }
    resp2 = requests.post(f"{BASE_URL}/api/admin/categories", headers=auth_headers, json=payload2)
    assert resp2.status_code == 201, f"Failed to create category 2: {resp2.text}"
    cat2 = resp2.json().get("category")
    categories.append(cat2)
    
    yield categories
    
    # Cleanup: Delete test categories
    for cat in categories:
        if cat and cat.get("id"):
            requests.delete(f"{BASE_URL}/api/admin/categories/{cat['id']}", headers=auth_headers)


class TestCategoryEditSlugUnchanged:
    """Test: PATCH /api/admin/categories/{id} with unchanged slug returns 200"""
    
    def test_patch_unchanged_slug_returns_200(self, auth_headers, test_categories):
        """
        Scenario: User opens edit modal, changes only name but slug stays same
        Expected: 200 OK (no false 409 conflict)
        """
        cat = test_categories[0]
        cat_id = cat["id"]
        original_slug = cat.get("slug") or f"test-cat-a-{int(time.time())}"
        
        # Patch with same slug, different name
        payload = {
            "name": f"Updated Name {int(time.time())}",
            "slug": original_slug  # Same slug - should NOT trigger conflict
        }
        resp = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat_id}",
            headers=auth_headers,
            json=payload
        )
        
        assert resp.status_code == 200, f"Expected 200 for unchanged slug, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "category" in data
        assert data["category"]["id"] == cat_id
        print(f"✓ PATCH unchanged slug returns 200 OK")


class TestCategorySlugConflict:
    """Test: Duplicate slug returns 409 with detail.field_name='slug'"""
    
    def test_patch_duplicate_slug_returns_409_with_field_name(self, auth_headers, test_categories):
        """
        Scenario: User tries to change category A's slug to category B's slug
        Expected: 409 with detail.field_name='slug' and detail.conflict.slug
        """
        cat_a = test_categories[0]
        cat_b = test_categories[1]
        
        # Try to set cat_a's slug to cat_b's slug
        payload = {
            "slug": cat_b.get("slug")  # Duplicate slug
        }
        resp = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat_a['id']}",
            headers=auth_headers,
            json=payload
        )
        
        assert resp.status_code == 409, f"Expected 409 for duplicate slug, got {resp.status_code}: {resp.text}"
        data = resp.json()
        detail = data.get("detail", {})
        
        # Verify field_name is 'slug'
        assert detail.get("field_name") == "slug", f"Expected field_name='slug', got {detail.get('field_name')}"
        assert detail.get("error_code") == "CATEGORY_SLUG_CONFLICT", f"Expected error_code='CATEGORY_SLUG_CONFLICT', got {detail.get('error_code')}"
        
        # Verify conflict object contains slug
        conflict = detail.get("conflict", {})
        assert "slug" in conflict, f"Expected conflict.slug, got {conflict}"
        print(f"✓ Duplicate slug returns 409 with field_name='slug' and conflict.slug='{conflict.get('slug')}'")


class TestCategoryParentIdValidation:
    """Test: Invalid parent_id returns 400 with detail.field_name='parent_id'"""
    
    def test_patch_invalid_parent_id_format_returns_400(self, auth_headers, test_categories):
        """
        Scenario: User sends malformed parent_id (not a valid UUID)
        Expected: 400 with detail.field_name='parent_id' and error_code='PARENT_ID_INVALID'
        """
        cat = test_categories[0]
        
        payload = {
            "parent_id": "invalid-uuid-format"  # Invalid UUID
        }
        resp = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat['id']}",
            headers=auth_headers,
            json=payload
        )
        
        assert resp.status_code == 400, f"Expected 400 for invalid parent_id format, got {resp.status_code}: {resp.text}"
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("field_name") == "parent_id", f"Expected field_name='parent_id', got {detail.get('field_name')}"
        assert detail.get("error_code") == "PARENT_ID_INVALID", f"Expected error_code='PARENT_ID_INVALID', got {detail.get('error_code')}"
        print(f"✓ Invalid parent_id format returns 400 with field_name='parent_id' and error_code='PARENT_ID_INVALID'")
    
    def test_patch_nonexistent_parent_id_returns_400(self, auth_headers, test_categories):
        """
        Scenario: User sends valid UUID format but non-existent parent_id
        Expected: 400 with detail.field_name='parent_id' and error_code='PARENT_ID_NOT_FOUND'
        """
        cat = test_categories[0]
        
        payload = {
            "parent_id": str(uuid.uuid4())  # Valid UUID but non-existent
        }
        resp = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat['id']}",
            headers=auth_headers,
            json=payload
        )
        
        assert resp.status_code == 400, f"Expected 400 for non-existent parent_id, got {resp.status_code}: {resp.text}"
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("field_name") == "parent_id", f"Expected field_name='parent_id', got {detail.get('field_name')}"
        assert detail.get("error_code") == "PARENT_ID_NOT_FOUND", f"Expected error_code='PARENT_ID_NOT_FOUND', got {detail.get('error_code')}"
        print(f"✓ Non-existent parent_id returns 400 with field_name='parent_id' and error_code='PARENT_ID_NOT_FOUND'")


class TestCategorySortOrderConflict:
    """Test: Sort order conflict returns 409 with detail.field_name='sort_order'"""
    
    def test_patch_duplicate_sort_order_returns_409(self, auth_headers, test_categories):
        """
        Scenario: User tries to set category A's sort_order to category B's sort_order
        Expected: 409 with detail.field_name='sort_order' and detail.conflict
        """
        cat_a = test_categories[0]
        cat_b = test_categories[1]
        
        payload = {
            "sort_order": cat_b.get("sort_order")  # Duplicate sort_order
        }
        resp = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat_a['id']}",
            headers=auth_headers,
            json=payload
        )
        
        assert resp.status_code == 409, f"Expected 409 for duplicate sort_order, got {resp.status_code}: {resp.text}"
        data = resp.json()
        detail = data.get("detail", {})
        
        assert detail.get("field_name") == "sort_order", f"Expected field_name='sort_order', got {detail.get('field_name')}"
        assert detail.get("error_code") == "ORDER_INDEX_ALREADY_USED", f"Expected error_code='ORDER_INDEX_ALREADY_USED', got {detail.get('error_code')}"
        
        conflict = detail.get("conflict", {})
        assert "sort_order" in conflict, f"Expected conflict.sort_order, got {conflict}"
        assert "slug" in conflict, f"Expected conflict.slug, got {conflict}"
        print(f"✓ Duplicate sort_order returns 409 with field_name='sort_order' and conflict info")


class TestParentModuleMismatch:
    """Test: Parent module mismatch returns 409 with detail.field_name='parent_id'"""
    
    def test_patch_parent_module_mismatch_returns_409(self, auth_headers, test_categories):
        """
        Scenario: User tries to set parent_id to a category with different module
        Expected: 409 with detail.field_name='parent_id' and error_code='PARENT_MODULE_MISMATCH'
        """
        # Create a vehicle module category
        timestamp = int(time.time())
        vehicle_payload = {
            "name": f"Vehicle Parent {timestamp}",
            "slug": f"vehicle-parent-{timestamp}",
            "module": "vehicle",
            "country_code": "DE",
            "sort_order": 9200 + timestamp % 100,
            "active_flag": True
        }
        vehicle_resp = requests.post(f"{BASE_URL}/api/admin/categories", headers=auth_headers, json=vehicle_payload)
        
        if vehicle_resp.status_code != 201:
            pytest.skip(f"Could not create vehicle category for test: {vehicle_resp.text}")
            return
        
        vehicle_cat = vehicle_resp.json().get("category")
        
        try:
            # Try to set 'other' module category's parent to 'vehicle' module category
            cat = test_categories[0]  # module: 'other'
            payload = {
                "parent_id": vehicle_cat["id"]  # Different module
            }
            resp = requests.patch(
                f"{BASE_URL}/api/admin/categories/{cat['id']}",
                headers=auth_headers,
                json=payload
            )
            
            assert resp.status_code == 409, f"Expected 409 for module mismatch, got {resp.status_code}: {resp.text}"
            data = resp.json()
            detail = data.get("detail", {})
            
            assert detail.get("field_name") == "parent_id", f"Expected field_name='parent_id', got {detail.get('field_name')}"
            assert detail.get("error_code") == "PARENT_MODULE_MISMATCH", f"Expected error_code='PARENT_MODULE_MISMATCH', got {detail.get('error_code')}"
            print(f"✓ Parent module mismatch returns 409 with field_name='parent_id' and error_code='PARENT_MODULE_MISMATCH'")
        finally:
            # Cleanup vehicle category
            requests.delete(f"{BASE_URL}/api/admin/categories/{vehicle_cat['id']}", headers=auth_headers)


class TestErrorDetailStructure:
    """Test: All error responses have consistent detail structure"""
    
    def test_error_detail_has_required_fields(self, auth_headers, test_categories):
        """
        Verify error responses contain: error_code, message, and optionally field_name/conflict
        """
        cat = test_categories[0]
        
        # Test invalid parent_id
        payload = {"parent_id": "invalid"}
        resp = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat['id']}",
            headers=auth_headers,
            json=payload
        )
        
        assert resp.status_code == 400
        detail = resp.json().get("detail", {})
        
        # Verify required fields
        assert "error_code" in detail, "Missing error_code in detail"
        assert "message" in detail, "Missing message in detail"
        assert isinstance(detail["error_code"], str), "error_code should be string"
        assert isinstance(detail["message"], str), "message should be string"
        
        # field_name should be present for field-specific errors
        assert "field_name" in detail, "Missing field_name in detail"
        print(f"✓ Error detail structure is correct: error_code, message, field_name")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
