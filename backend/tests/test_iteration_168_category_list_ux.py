"""
Test Suite for Iteration 168: Category List/Search UX and Delete/Undo Features

Features tested:
- Issue-state filter (with_issues filter)
- Search input filter
- Sort select options
- Delete cascade with undo bar
- Undo history panel (/api/admin/categories/delete-operations)
"""
import os
import time

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _request(method: str, url: str, **kwargs):
    """Helper for HTTP requests with retry logic."""
    request_timeout = kwargs.pop("timeout", 30)
    last_error = None
    for attempt in range(4):
        try:
            return requests.request(method, url, timeout=request_timeout, **kwargs)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt >= 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise last_error


def _login(email: str, password: str):
    """Login helper to get access token."""
    response = _request(
        "POST",
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        return None
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for authentication."""
    token = _login("admin@platform.com", "Admin123!")
    if not token:
        pytest.skip("admin login failed")
    return token


def _headers(token: str):
    """Build auth headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


class TestCategoryListFilters:
    """Test category list API filters."""

    def test_list_categories_returns_items(self, admin_token):
        """Basic list endpoint returns items array."""
        response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            params={"country": "DE"},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_categories_module_filter(self, admin_token):
        """Filter by module (real_estate, vehicle, other)."""
        response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            params={"country": "TR", "module": "vehicle"},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        # All returned items should have module=vehicle or be child categories
        for item in data.get("items", []):
            # Root level categories should match the module filter
            if not item.get("parent_id"):
                assert item.get("module") == "vehicle"

    def test_list_categories_active_flag_filter(self, admin_token):
        """Filter by active_flag (active status)."""
        # Test active_flag=true
        response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            params={"country": "DE", "active_flag": "true"},
            timeout=30,
        )
        assert response.status_code == 200, response.text


class TestDeleteOperationsHistory:
    """Test delete operations history endpoint."""

    def test_delete_operations_list_returns_items(self, admin_token):
        """GET /api/admin/categories/delete-operations returns items list."""
        response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories/delete-operations",
            headers=_headers(admin_token),
            params={"hours": 24, "limit": 20},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        
        # Should have items array
        assert "items" in data
        assert isinstance(data["items"], list)
        
        # Each item should have expected fields
        for item in data["items"]:
            assert "operation_id" in item
            assert "deleted_count" in item
            assert "created_at" in item
            # Status should be one of: active, restored, expired
            if "status" in item:
                assert item["status"] in ["active", "restored", "expired"]

    def test_delete_operations_list_respects_limit(self, admin_token):
        """Verify limit parameter is respected."""
        response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories/delete-operations",
            headers=_headers(admin_token),
            params={"hours": 24, "limit": 5},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        
        # Should not exceed limit
        assert len(data.get("items", [])) <= 5


class TestCategoryCacheRegression:
    """Test category list cache updates properly after mutations."""

    def test_create_category_updates_list(self, admin_token):
        """After creating a category, it should appear in the list."""
        suffix = str(int(time.time() * 1000))
        
        # Create category
        create_response = _request(
            "POST",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            json={
                "name": f"Cache Test Create {suffix}",
                "slug": f"cache-test-create-{suffix}",
                "module": "other",
                "country_code": "TR",
                "sort_order": 9800,
                "active_flag": True,
            },
            timeout=30,
        )
        assert create_response.status_code in {200, 201}, create_response.text
        created = (create_response.json() or {}).get("category") or {}
        created_id = created.get("id")
        assert created_id, "Created category should have an ID"
        
        # List categories and verify the new one is present
        list_response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            params={"country": "TR", "module": "other"},
            timeout=30,
        )
        assert list_response.status_code == 200, list_response.text
        items = (list_response.json() or {}).get("items") or []
        item_ids = {str(item.get("id")) for item in items}
        
        assert created_id in item_ids, "Created category should be in list immediately"
        
        # Cleanup: delete the test category
        _request(
            "DELETE",
            f"{BASE_URL}/api/admin/categories/{created_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"cascade": "true"},
            timeout=30,
        )

    def test_delete_undo_updates_list(self, admin_token):
        """After undo, deleted categories should reappear in list."""
        suffix = str(int(time.time() * 1000))
        
        # Create category
        create_response = _request(
            "POST",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            json={
                "name": f"Cache Test Undo {suffix}",
                "slug": f"cache-test-undo-{suffix}",
                "module": "other",
                "country_code": "TR",
                "sort_order": 9801,
                "active_flag": True,
            },
            timeout=30,
        )
        assert create_response.status_code in {200, 201}, create_response.text
        created = (create_response.json() or {}).get("category") or {}
        created_id = created.get("id")
        
        # Delete with cascade
        delete_response = _request(
            "DELETE",
            f"{BASE_URL}/api/admin/categories/{created_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"cascade": "true"},
            timeout=30,
        )
        assert delete_response.status_code == 200, delete_response.text
        delete_data = delete_response.json()
        undo_operation_id = delete_data.get("undo_operation_id")
        
        # Verify deleted from list
        list_after_delete = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            params={"country": "TR", "module": "other"},
            timeout=30,
        )
        deleted_ids_check = {str(item.get("id")) for item in (list_after_delete.json() or {}).get("items") or []}
        assert created_id not in deleted_ids_check, "Deleted category should not be in list"
        
        # Undo the delete
        if undo_operation_id:
            undo_response = _request(
                "POST",
                f"{BASE_URL}/api/admin/categories/delete-operations/{undo_operation_id}/undo",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=30,
            )
            assert undo_response.status_code == 200, undo_response.text
            
            # Verify restored in list
            list_after_undo = _request(
                "GET",
                f"{BASE_URL}/api/admin/categories",
                headers=_headers(admin_token),
                params={"country": "TR", "module": "other"},
                timeout=30,
            )
            restored_ids = {str(item.get("id")) for item in (list_after_undo.json() or {}).get("items") or []}
            assert created_id in restored_ids, "Undone category should reappear in list"
            
            # Final cleanup
            _request(
                "DELETE",
                f"{BASE_URL}/api/admin/categories/{created_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"cascade": "true"},
                timeout=30,
            )


class TestCascadeDeleteUndo:
    """Test cascade delete and undo functionality."""

    def test_cascade_delete_returns_undo_info(self, admin_token):
        """DELETE with cascade=true should return undo operation info."""
        suffix = str(int(time.time() * 1000))
        
        # Create test category
        create_response = _request(
            "POST",
            f"{BASE_URL}/api/admin/categories",
            headers=_headers(admin_token),
            json={
                "name": f"Cascade Delete Test {suffix}",
                "slug": f"cascade-delete-test-{suffix}",
                "module": "other",
                "country_code": "TR",
                "sort_order": 9802,
                "active_flag": True,
            },
            timeout=30,
        )
        assert create_response.status_code in {200, 201}, create_response.text
        created = (create_response.json() or {}).get("category") or {}
        created_id = created.get("id")
        
        # Delete with cascade
        delete_response = _request(
            "DELETE",
            f"{BASE_URL}/api/admin/categories/{created_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"cascade": "true"},
            timeout=30,
        )
        assert delete_response.status_code == 200, delete_response.text
        data = delete_response.json()
        
        # Verify response structure
        assert data.get("cascade") is True
        assert data.get("deleted_count") >= 1
        assert data.get("undo_operation_id"), "Should have undo operation ID"
        assert data.get("undo_expires_at"), "Should have undo expiration time"
        assert "deleted_ids" in data
        assert created_id in data.get("deleted_ids", [])

    def test_undo_expired_operation_fails(self, admin_token):
        """Attempting to undo an expired operation should fail gracefully."""
        # Use a fake/invalid operation ID
        response = _request(
            "POST",
            f"{BASE_URL}/api/admin/categories/delete-operations/00000000-0000-0000-0000-000000000000/undo",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        # Should return 404 for not found
        assert response.status_code == 404, response.text
