"""
Test: PATCH /api/admin/categories/{id} - Slug Conflict Fix (P0 Bug)
Problem: When editing a category without changing the slug, a 409 slug conflict was returned
Fix: Backend now only checks duplicate slug if slug is actually being changed

Test Cases:
1. Same slug update (no change) should succeed with 200
2. Different slug update (actual change) should check duplicates
3. Duplicate slug to another category should return 409
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Problematic category id mentioned in context
PROBLEMATIC_CATEGORY_ID = "21b5a831-0ee8-438b-a68b-6b8d4dae7f43"


@pytest.fixture(scope="module")
def auth_headers():
    """Login as admin and get auth headers"""
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {
        "email": "admin@platform.com",
        "password": "Admin123!"
    }
    response = requests.post(login_url, json=login_payload)
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    data = response.json()
    token = data.get("access_token")
    if not token:
        pytest.skip("No access token returned")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def get_category_for_testing(auth_headers):
    """Fetch an existing category for testing or find one"""
    # First try the problematic category
    response = requests.get(
        f"{BASE_URL}/api/admin/categories/{PROBLEMATIC_CATEGORY_ID}",
        headers=auth_headers
    )
    if response.status_code == 200:
        return response.json()
    
    # Fallback: get any category from the list
    list_response = requests.get(
        f"{BASE_URL}/api/admin/categories?limit=10",
        headers=auth_headers
    )
    if list_response.status_code != 200:
        pytest.skip("Cannot fetch categories list")
    
    data = list_response.json()
    items = data.get("items", [])
    if not items:
        pytest.skip("No categories found for testing")
    return items[0]


class TestCategorySlugConflictFix:
    """Test suite for P0 slug conflict fix when editing categories"""

    def test_same_slug_update_should_succeed(self, auth_headers, get_category_for_testing):
        """
        Test: PATCH category with the same slug should NOT return 409
        This is the main P0 fix - editing without changing slug should work
        """
        category = get_category_for_testing
        category_id = category.get("id")
        current_slug = category.get("slug")
        current_name = category.get("name")
        
        assert category_id, "Category ID is required"
        
        # If slug is a dict (i18n), extract the primary slug
        if isinstance(current_slug, dict):
            current_slug = current_slug.get("tr") or current_slug.get("de") or list(current_slug.values())[0]
        
        print(f"Testing category: {category_id}, slug: {current_slug}, name: {current_name}")
        
        # PATCH with the same slug value
        patch_payload = {
            "slug": current_slug,
            "name": current_name  # Keep name same too
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=auth_headers,
            json=patch_payload
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:500] if response.text else 'Empty'}")
        
        # P0 Fix: Same slug should return 200, not 409
        assert response.status_code == 200, \
            f"Same slug update should succeed (200), got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "category" in data, "Response should contain 'category' key"
        print("PASS: Same slug update succeeded without 409 conflict")

    def test_update_only_name_without_slug(self, auth_headers, get_category_for_testing):
        """
        Test: PATCH category changing only name (no slug field) should succeed
        """
        category = get_category_for_testing
        category_id = category.get("id")
        current_name = category.get("name") or "Test Category"
        
        # Just update name, don't send slug at all
        new_name = f"{current_name} (updated)"
        patch_payload = {
            "name": new_name
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=auth_headers,
            json=patch_payload
        )
        
        print(f"Name-only update response: {response.status_code}")
        
        # Should succeed without slug conflict
        assert response.status_code == 200, \
            f"Name-only update should succeed, got {response.status_code}: {response.text}"
        
        # Restore original name
        restore_payload = {"name": current_name}
        requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=auth_headers,
            json=restore_payload
        )
        print("PASS: Name-only update succeeded")

    def test_duplicate_slug_should_return_409(self, auth_headers):
        """
        Test: PATCH with a slug that belongs to another category SHOULD return 409
        This ensures duplicate slug protection still works when actually changing slug
        """
        # Get multiple categories to test cross-conflict
        list_response = requests.get(
            f"{BASE_URL}/api/admin/categories?limit=20",
            headers=auth_headers
        )
        if list_response.status_code != 200:
            pytest.skip("Cannot fetch categories")
        
        items = list_response.json().get("items", [])
        if len(items) < 2:
            pytest.skip("Need at least 2 categories for duplicate test")
        
        # Pick two different categories
        cat1 = items[0]
        cat2 = None
        for item in items[1:]:
            # Find a category with a different slug
            slug1 = cat1.get("slug")
            slug2 = item.get("slug")
            if isinstance(slug1, dict):
                slug1 = slug1.get("tr") or list(slug1.values())[0]
            if isinstance(slug2, dict):
                slug2 = slug2.get("tr") or list(slug2.values())[0]
            if slug1 != slug2:
                cat2 = item
                break
        
        if not cat2:
            pytest.skip("Cannot find two categories with different slugs")
        
        cat1_id = cat1.get("id")
        cat2_slug = cat2.get("slug")
        if isinstance(cat2_slug, dict):
            cat2_slug = cat2_slug.get("tr") or list(cat2_slug.values())[0]
        
        print(f"Testing: Update category {cat1_id} to use slug '{cat2_slug}' which belongs to another category")
        
        # Try to update cat1 with cat2's slug - should fail with 409
        patch_payload = {
            "slug": cat2_slug
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat1_id}",
            headers=auth_headers,
            json=patch_payload
        )
        
        print(f"Duplicate slug update response: {response.status_code}")
        
        # Should return 409 for actual duplicate
        assert response.status_code == 409, \
            f"Duplicate slug update should return 409, got {response.status_code}"
        
        # Verify error message mentions slug
        error_detail = response.json().get("detail", "")
        assert "slug" in error_detail.lower(), \
            f"Error should mention slug conflict, got: {error_detail}"
        
        print("PASS: Duplicate slug correctly blocked with 409")


class TestSpecificProblemCategory:
    """Test the specific problematic category mentioned in the bug report"""

    def test_problematic_category_patch(self, auth_headers):
        """
        Test: PATCH the specific category ID mentioned in the bug report
        ID: 21b5a831-0ee8-438b-a68b-6b8d4dae7f43
        """
        # First check if this category exists
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/{PROBLEMATIC_CATEGORY_ID}",
            headers=auth_headers
        )
        
        if response.status_code == 404:
            pytest.skip("Problematic category not found in database")
        
        if response.status_code != 200:
            pytest.skip(f"Cannot fetch problematic category: {response.status_code}")
        
        category = response.json()
        current_slug = category.get("slug")
        current_name = category.get("name")
        
        if isinstance(current_slug, dict):
            current_slug = current_slug.get("tr") or list(current_slug.values())[0]
        
        print(f"Testing problematic category: {PROBLEMATIC_CATEGORY_ID}")
        print(f"Current slug: {current_slug}, name: {current_name}")
        
        # PATCH with same data
        patch_payload = {
            "slug": current_slug,
            "name": current_name
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{PROBLEMATIC_CATEGORY_ID}",
            headers=auth_headers,
            json=patch_payload
        )
        
        print(f"PATCH response status: {response.status_code}")
        
        # Should return 200, not 409
        assert response.status_code == 200, \
            f"Problematic category PATCH should succeed, got {response.status_code}: {response.text}"
        
        print("PASS: Problematic category can now be saved without false 409")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
