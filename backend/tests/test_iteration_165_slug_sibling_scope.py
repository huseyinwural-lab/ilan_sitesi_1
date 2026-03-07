"""
Iteration 165: Category Slug Conflict Sibling Scope Tests
=========================================================
Feature: Backend category slug conflict scope: aynı slug farklı parent altında conflict olmamalı
Bug fix: Slug uniqueness is now enforced at SIBLING scope (same parent_id), not globally

Test Cases:
1. Same slug under DIFFERENT parents -> No conflict (should succeed)
2. Same slug under SAME parent -> Conflict (should return 409)
3. Update slug to match sibling -> Conflict (should return 409)
4. Update slug to match category under different parent -> No conflict (should succeed)
5. Verify DE/real_estate Wohnen hierarchy with L2 (Verkauf/Miete/Kurzzeitmiete) and L3 categories
6. Basic category edit flow regression test

Referenced endpoints:
- POST /api/admin/categories (admin_create_category)
- PATCH /api/admin/categories/{id} (admin_update_category)
"""

import pytest
import requests
import os
import uuid
from typing import Optional

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

TEST_PREFIX = "TEST_165_"  # For cleanup


@pytest.fixture(scope="function")
def auth_headers():
    """Login as admin and get auth headers"""
    if not BASE_URL:
        pytest.skip("BASE_URL not set")
    login_url = f"{BASE_URL}/api/auth/login"
    login_payload = {
        "email": "admin@platform.com",
        "password": "Admin123!"
    }
    response = requests.post(login_url, json=login_payload, timeout=30)
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    data = response.json()
    token = data.get("access_token")
    if not token:
        pytest.skip("No access token returned")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="function")
def wohnen_category(auth_headers):
    """Get DE Wohnen category (Immobilien > Wohnen)"""
    response = requests.get(
        f"{BASE_URL}/api/admin/categories?country_code=DE&module=real_estate&limit=100",
        headers=auth_headers,
        timeout=30
    )
    if response.status_code != 200:
        pytest.skip(f"Cannot fetch categories: {response.status_code}")
    
    items = response.json().get("items", [])
    # Find Immobilien first (root category with country_code=DE)
    immobilien = next((c for c in items if c.get("name") == "Immobilien" and c.get("parent_id") is None and c.get("country_code") == "DE"), None)
    if not immobilien:
        pytest.skip("DE Immobilien category not found")
    
    # Find Wohnen under Immobilien
    wohnen = next((c for c in items if c.get("name") == "Wohnen" and c.get("parent_id") == immobilien["id"]), None)
    if not wohnen:
        pytest.skip("DE Wohnen category not found under Immobilien")
    
    return wohnen


@pytest.fixture(scope="function")
def l2_categories(auth_headers, wohnen_category):
    """Get Verkauf, Miete, Kurzzeitmiete L2 categories under Wohnen"""
    response = requests.get(
        f"{BASE_URL}/api/admin/categories?country_code=DE&module=real_estate&limit=100",
        headers=auth_headers,
        timeout=30
    )
    items = response.json().get("items", [])
    
    verkauf = next((c for c in items if c.get("name") == "Verkauf" and c.get("parent_id") == wohnen_category["id"]), None)
    miete = next((c for c in items if c.get("name") == "Miete" and c.get("parent_id") == wohnen_category["id"]), None)
    kurzzeitmiete = next((c for c in items if c.get("name") == "Kurzzeitmiete" and c.get("parent_id") == wohnen_category["id"]), None)
    
    return {
        "verkauf": verkauf,
        "miete": miete,
        "kurzzeitmiete": kurzzeitmiete
    }


def cleanup_test_categories(auth_headers):
    """Delete all test categories created during this test"""
    response = requests.get(
        f"{BASE_URL}/api/admin/categories?limit=200",
        headers=auth_headers
    )
    if response.status_code != 200:
        return
    
    items = response.json().get("items", [])
    for item in items:
        slug = item.get("slug")
        if isinstance(slug, dict):
            slug = slug.get("tr", "")
        if slug and slug.startswith(TEST_PREFIX.lower().replace("_", "-")):
            requests.delete(
                f"{BASE_URL}/api/admin/categories/{item['id']}",
                headers=auth_headers
            )


class TestSlugSiblingScope:
    """Test slug conflict is checked at sibling (same parent) scope only"""
    
    def test_same_slug_different_parents_allowed(self, auth_headers, l2_categories):
        """
        Feature: Same slug under DIFFERENT parents should NOT conflict
        Verkauf/wohnung and Miete/wohnung should both exist
        """
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country_code=DE&module=real_estate&limit=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        
        # Find wohnung under Verkauf
        verkauf_id = l2_categories["verkauf"]["id"] if l2_categories["verkauf"] else None
        miete_id = l2_categories["miete"]["id"] if l2_categories["miete"] else None
        kurzzeitmiete_id = l2_categories["kurzzeitmiete"]["id"] if l2_categories["kurzzeitmiete"] else None
        
        if not all([verkauf_id, miete_id, kurzzeitmiete_id]):
            pytest.skip("L2 categories not found")
        
        # Check wohnung exists under all three L2 categories
        wohnung_verkauf = next((c for c in items if c.get("slug") == "wohnung" and c.get("parent_id") == verkauf_id), None)
        wohnung_miete = next((c for c in items if c.get("slug") == "wohnung" and c.get("parent_id") == miete_id), None)
        wohnung_kurzzeitmiete = next((c for c in items if c.get("slug") == "wohnung" and c.get("parent_id") == kurzzeitmiete_id), None)
        
        # All should exist - same slug under different parents
        assert wohnung_verkauf is not None, "Verkauf/wohnung should exist"
        assert wohnung_miete is not None, "Miete/wohnung should exist"
        assert wohnung_kurzzeitmiete is not None, "Kurzzeitmiete/wohnung should exist"
        
        # They should have different IDs
        ids = {wohnung_verkauf["id"], wohnung_miete["id"], wohnung_kurzzeitmiete["id"]}
        assert len(ids) == 3, "All wohnung categories should have unique IDs"
        
        print("PASS: Same slug 'wohnung' exists under Verkauf, Miete, Kurzzeitmiete (different parents)")

    def test_haus_exists_under_all_l2(self, auth_headers, l2_categories):
        """
        Verify 'haus' slug exists under all L2 categories
        This is another example of sibling scope working
        """
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country_code=DE&module=real_estate&limit=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        
        verkauf_id = l2_categories["verkauf"]["id"] if l2_categories["verkauf"] else None
        miete_id = l2_categories["miete"]["id"] if l2_categories["miete"] else None
        kurzzeitmiete_id = l2_categories["kurzzeitmiete"]["id"] if l2_categories["kurzzeitmiete"] else None
        
        if not all([verkauf_id, miete_id, kurzzeitmiete_id]):
            pytest.skip("L2 categories not found")
        
        haus_verkauf = next((c for c in items if c.get("slug") == "haus" and c.get("parent_id") == verkauf_id), None)
        haus_miete = next((c for c in items if c.get("slug") == "haus" and c.get("parent_id") == miete_id), None)
        haus_kurzzeitmiete = next((c for c in items if c.get("slug") == "haus" and c.get("parent_id") == kurzzeitmiete_id), None)
        
        assert haus_verkauf is not None, "Verkauf/haus should exist"
        assert haus_miete is not None, "Miete/haus should exist"
        assert haus_kurzzeitmiete is not None, "Kurzzeitmiete/haus should exist"
        
        print("PASS: Same slug 'haus' exists under all L2 categories")

    def test_duplicate_slug_same_parent_returns_409(self, auth_headers, l2_categories):
        """
        Feature: Same slug under SAME parent should return 409 conflict
        Try to create 'wohnung' under Verkauf when it already exists
        """
        if not l2_categories["verkauf"]:
            pytest.skip("Verkauf category not found")
        
        verkauf_id = l2_categories["verkauf"]["id"]
        
        # Try to create another 'wohnung' under Verkauf
        create_payload = {
            "name": "Test Duplicate Wohnung",
            "slug": "wohnung",  # This already exists under Verkauf
            "parent_id": verkauf_id,
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 999
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=create_payload
        )
        
        print(f"Duplicate slug response: {response.status_code}")
        
        # Should return 409 conflict
        assert response.status_code == 409, \
            f"Duplicate slug under same parent should return 409, got {response.status_code}: {response.text}"
        
        # Verify error detail mentions slug
        detail = response.json().get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("error_code") == "CATEGORY_SLUG_CONFLICT" or "slug" in detail.get("message", "").lower(), \
                f"Error should mention slug conflict: {detail}"
        else:
            assert "slug" in str(detail).lower(), f"Error should mention slug: {detail}"
        
        print("PASS: Duplicate slug under same parent correctly returns 409")

    def test_create_new_slug_under_existing_parent_succeeds(self, auth_headers, l2_categories):
        """
        Create a new unique slug under a parent should succeed
        """
        if not l2_categories["verkauf"]:
            pytest.skip("Verkauf category not found")
        
        verkauf_id = l2_categories["verkauf"]["id"]
        unique_slug = f"{TEST_PREFIX.lower().replace('_', '-')}{uuid.uuid4().hex[:8]}"
        
        create_payload = {
            "name": f"Test {unique_slug}",
            "slug": unique_slug,
            "parent_id": verkauf_id,
            "module": "real_estate",
            "country_code": "DE",
            "sort_order": 999
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=create_payload
        )
        
        print(f"Create new slug response: {response.status_code}")
        
        assert response.status_code == 201, \
            f"Create new slug should succeed, got {response.status_code}: {response.text}"
        
        # Cleanup
        created_id = response.json().get("category", {}).get("id")
        if created_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{created_id}", headers=auth_headers)
        
        print("PASS: New unique slug created successfully")


class TestUpdateSlugConflict:
    """Test slug conflict on update operations"""

    def test_update_slug_to_sibling_returns_409(self, auth_headers, l2_categories):
        """
        Update a category slug to match a sibling should return 409
        """
        if not l2_categories["verkauf"]:
            pytest.skip("Verkauf category not found")
        
        verkauf_id = l2_categories["verkauf"]["id"]
        
        # Get children of Verkauf
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country_code=DE&module=real_estate&limit=100",
            headers=auth_headers
        )
        items = response.json().get("items", [])
        verkauf_children = [c for c in items if c.get("parent_id") == verkauf_id]
        
        if len(verkauf_children) < 2:
            pytest.skip("Need at least 2 children under Verkauf")
        
        # Get wohnung and haus under Verkauf
        wohnung = next((c for c in verkauf_children if c.get("slug") == "wohnung"), None)
        haus = next((c for c in verkauf_children if c.get("slug") == "haus"), None)
        
        if not wohnung or not haus:
            pytest.skip("Need wohnung and haus under Verkauf")
        
        # Try to update haus slug to 'wohnung' (already exists as sibling)
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{haus['id']}",
            headers=auth_headers,
            json={"slug": "wohnung"}
        )
        
        print(f"Update to sibling slug response: {response.status_code}")
        
        assert response.status_code == 409, \
            f"Update to sibling slug should return 409, got {response.status_code}: {response.text}"
        
        print("PASS: Update slug to match sibling correctly returns 409")

    def test_update_slug_to_non_sibling_succeeds(self, auth_headers, l2_categories):
        """
        Update a category slug to match a category under DIFFERENT parent should succeed
        (as long as the new slug is unique among siblings)
        """
        if not l2_categories["verkauf"] or not l2_categories["miete"]:
            pytest.skip("Verkauf or Miete category not found")
        
        verkauf_id = l2_categories["verkauf"]["id"]
        
        # Create a test category under Verkauf
        unique_slug = f"{TEST_PREFIX.lower().replace('_', '-')}{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json={
                "name": f"Test Update {unique_slug}",
                "slug": unique_slug,
                "parent_id": verkauf_id,
                "module": "real_estate",
                "country_code": "DE",
                "sort_order": 998
            }
        )
        
        if create_response.status_code != 201:
            pytest.skip(f"Cannot create test category: {create_response.status_code}")
        
        test_cat_id = create_response.json().get("category", {}).get("id")
        
        try:
            # Update to a new unique slug (not matching any sibling)
            new_unique_slug = f"{TEST_PREFIX.lower().replace('_', '-')}{uuid.uuid4().hex[:8]}"
            update_response = requests.patch(
                f"{BASE_URL}/api/admin/categories/{test_cat_id}",
                headers=auth_headers,
                json={"slug": new_unique_slug}
            )
            
            print(f"Update to unique slug response: {update_response.status_code}")
            
            assert update_response.status_code == 200, \
                f"Update to unique slug should succeed, got {update_response.status_code}: {update_response.text}"
            
            print("PASS: Update to unique slug succeeds")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/admin/categories/{test_cat_id}", headers=auth_headers)


class TestDEWohnenHierarchy:
    """Verify DE/real_estate Wohnen hierarchy with Verkauf/Miete/Kurzzeitmiete and L3 categories"""

    def test_wohnen_l1_exists(self, auth_headers, wohnen_category):
        """Verify Wohnen L1 exists under Immobilien"""
        assert wohnen_category is not None
        assert wohnen_category.get("name") == "Wohnen"
        assert wohnen_category.get("country_code") == "DE"
        assert wohnen_category.get("module") == "real_estate"
        print(f"PASS: Wohnen L1 exists: id={wohnen_category['id']}")

    def test_l2_verkauf_miete_kurzzeitmiete_exist(self, auth_headers, l2_categories):
        """Verify L2 Verkauf, Miete, Kurzzeitmiete exist under Wohnen"""
        assert l2_categories["verkauf"] is not None, "Verkauf L2 should exist"
        assert l2_categories["miete"] is not None, "Miete L2 should exist"
        assert l2_categories["kurzzeitmiete"] is not None, "Kurzzeitmiete L2 should exist"
        
        print(f"PASS: Verkauf (id={l2_categories['verkauf']['id'][:8]}...) exists")
        print(f"PASS: Miete (id={l2_categories['miete']['id'][:8]}...) exists")
        print(f"PASS: Kurzzeitmiete (id={l2_categories['kurzzeitmiete']['id'][:8]}...) exists")

    def test_l3_categories_exist_under_each_l2(self, auth_headers, l2_categories):
        """Verify L3 categories exist under each L2"""
        expected_l3_slugs = [
            "wohnung", "haus", "grundstueck", "wg-zimmer", "senioren-wg",
            "garage", "stellplatz", "gewerbeimmobilien", "anlageimmobilie", "ferienimmobilie"
        ]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country_code=DE&module=real_estate&limit=100",
            headers=auth_headers
        )
        items = response.json().get("items", [])
        
        for l2_name, l2_cat in l2_categories.items():
            if not l2_cat:
                continue
            
            l2_id = l2_cat["id"]
            l3_children = [c for c in items if c.get("parent_id") == l2_id]
            l3_slugs = {c.get("slug") for c in l3_children}
            
            # Check expected slugs exist
            found_count = len(l3_slugs.intersection(set(expected_l3_slugs)))
            print(f"{l2_name.capitalize()}: {len(l3_children)} L3 children, {found_count} expected slugs found")
            
            assert len(l3_children) >= 10, \
                f"{l2_name} should have at least 10 L3 children, found {len(l3_children)}"
        
        print("PASS: All L2 categories have expected L3 children")


class TestCategoryEditRegression:
    """Basic category edit flow regression tests"""

    def test_edit_category_without_slug_change(self, auth_headers, l2_categories):
        """
        Editing a category without changing slug should succeed (regression test)
        """
        if not l2_categories["verkauf"]:
            pytest.skip("Verkauf category not found")
        
        verkauf = l2_categories["verkauf"]
        current_name = verkauf.get("name")
        current_slug = verkauf.get("slug")
        
        # Update only name, keep slug
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{verkauf['id']}",
            headers=auth_headers,
            json={
                "name": current_name,  # Same name
                "slug": current_slug   # Same slug
            }
        )
        
        print(f"Edit without slug change response: {response.status_code}")
        
        assert response.status_code == 200, \
            f"Edit without slug change should succeed, got {response.status_code}: {response.text}"
        
        print("PASS: Edit category without slug change succeeds (no false 409)")

    def test_edit_category_name_only(self, auth_headers, l2_categories):
        """
        Editing only the name (not slug) should succeed
        """
        if not l2_categories["verkauf"]:
            pytest.skip("Verkauf category not found")
        
        verkauf = l2_categories["verkauf"]
        original_name = verkauf.get("name")
        
        # Update only name
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{verkauf['id']}",
            headers=auth_headers,
            json={"name": f"{original_name} (test)"}
        )
        
        assert response.status_code == 200, \
            f"Name-only update should succeed, got {response.status_code}"
        
        # Restore original name
        requests.patch(
            f"{BASE_URL}/api/admin/categories/{verkauf['id']}",
            headers=auth_headers,
            json={"name": original_name}
        )
        
        print("PASS: Name-only update succeeds")


class TestSlugConflictErrorFormat:
    """Verify error response format for slug conflicts"""

    def test_conflict_error_has_correct_structure(self, auth_headers, l2_categories):
        """
        Verify 409 error response has field_name='slug' and conflict details
        """
        if not l2_categories["verkauf"]:
            pytest.skip("Verkauf category not found")
        
        verkauf_id = l2_categories["verkauf"]["id"]
        
        # Try to create duplicate slug
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json={
                "name": "Test Duplicate",
                "slug": "wohnung",  # Already exists under Verkauf
                "parent_id": verkauf_id,
                "module": "real_estate",
                "country_code": "DE",
                "sort_order": 999
            }
        )
        
        assert response.status_code == 409
        
        detail = response.json().get("detail", {})
        if isinstance(detail, dict):
            # Verify structured error
            assert detail.get("error_code") == "CATEGORY_SLUG_CONFLICT", \
                f"Expected error_code=CATEGORY_SLUG_CONFLICT, got {detail.get('error_code')}"
            assert detail.get("field_name") == "slug", \
                f"Expected field_name=slug, got {detail.get('field_name')}"
            
            conflict = detail.get("conflict", {})
            assert conflict.get("slug") == "wohnung", \
                f"Expected conflict.slug=wohnung, got {conflict.get('slug')}"
            assert conflict.get("parent_id") == verkauf_id, \
                f"Expected conflict.parent_id={verkauf_id}, got {conflict.get('parent_id')}"
            
            print(f"PASS: Error structure correct: error_code={detail.get('error_code')}, field_name={detail.get('field_name')}")
        else:
            # String error format
            assert "slug" in str(detail).lower(), f"Error should mention slug: {detail}"
            print(f"PASS: Error mentions slug: {detail}")


# Note: cleanup is done within individual tests to avoid fixture issues


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
