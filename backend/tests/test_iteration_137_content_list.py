"""
Iteration 137: Content List API Tests for Admin Content Builder
=================================================================
Tests:
- GET /api/admin/layouts with draft+published status filter
- GET /api/admin/layouts with include_deleted=true
- DELETE /api/admin/layouts/{revision_id} soft-delete
- POST /api/admin/layouts/{revision_id}/copy copy functionality
"""

import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@platform.com",
        "password": "Admin123!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin login failed - skipping authenticated tests")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAdminLayoutsList:
    """Test GET /api/admin/layouts endpoint"""
    
    def test_list_layouts_default(self, auth_headers):
        """Test default list (draft+published, no deleted)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"statuses": "draft,published"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should have items array"
        assert "pagination" in data, "Response should have pagination object"
        
        # Verify items structure
        if data["items"]:
            item = data["items"][0]
            assert "id" in item or "revision_id" in item, "Item should have id or revision_id"
            assert "page_type" in item, "Item should have page_type"
            assert "country" in item, "Item should have country"
            assert "module" in item, "Item should have module"
            assert "status" in item, "Item should have status"
            assert "is_deleted" in item, "Item should have is_deleted flag"
            
            # Verify is_deleted is False (default behavior)
            for item in data["items"]:
                assert item.get("is_deleted") == False, "Default list should not include deleted items"
                assert item.get("status") in ["draft", "published"], f"Status should be draft or published, got {item.get('status')}"
        
        print(f"SUCCESS: List layouts returned {len(data['items'])} items")
    
    def test_list_layouts_with_deleted(self, auth_headers):
        """Test list with include_deleted=true"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={
                "include_deleted": True,
                "statuses": "draft,published"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should have items array"
        
        # May include deleted items now
        print(f"SUCCESS: List with deleted returned {len(data['items'])} items")
        
        deleted_count = sum(1 for item in data["items"] if item.get("is_deleted"))
        print(f"  - Deleted items count: {deleted_count}")
    
    def test_list_layouts_pagination(self, auth_headers):
        """Test pagination parameters"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={
                "page": 1,
                "limit": 10
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
        assert "total" in data["pagination"]
        
        print(f"SUCCESS: Pagination works - total: {data['pagination']['total']}")


class TestAdminLayoutSoftDelete:
    """Test DELETE /api/admin/layouts/{revision_id} soft-delete"""
    
    def test_soft_delete_nonexistent(self, auth_headers):
        """Test soft-delete with nonexistent revision_id"""
        fake_uuid = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/admin/layouts/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404 for nonexistent, got {response.status_code}"
        print("SUCCESS: Nonexistent revision returns 404")
    
    def test_soft_delete_invalid_uuid(self, auth_headers):
        """Test soft-delete with invalid UUID"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/layouts/invalid-uuid",
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid UUID, got {response.status_code}"
        print("SUCCESS: Invalid UUID returns 400")
    
    def test_soft_delete_existing_revision(self, auth_headers):
        """Test soft-delete on an existing draft revision"""
        # First, get a draft revision from the list
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"statuses": "draft", "limit": 10}
        )
        
        if list_response.status_code != 200 or not list_response.json().get("items"):
            pytest.skip("No draft revisions available to test soft-delete")
        
        draft_item = None
        for item in list_response.json()["items"]:
            if item.get("status") == "draft" and not item.get("is_deleted"):
                draft_item = item
                break
        
        if not draft_item:
            pytest.skip("No non-deleted draft revision available for soft-delete test")
        
        revision_id = draft_item.get("revision_id") or draft_item.get("id")
        
        # Perform soft-delete
        response = requests.delete(
            f"{BASE_URL}/api/admin/layouts/{revision_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") == True, "Response should have ok=True"
        assert "item" in data, "Response should have item object"
        assert data["item"].get("is_deleted") == True, "Item should be marked as deleted"
        
        print(f"SUCCESS: Soft-delete worked for revision {revision_id}")
        
        # Verify the item now shows as deleted in list with include_deleted
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": True, "statuses": "draft,published"}
        )
        if verify_response.status_code == 200:
            items = verify_response.json().get("items", [])
            found = next((i for i in items if (i.get("revision_id") or i.get("id")) == revision_id), None)
            if found:
                assert found.get("is_deleted") == True, "Deleted item should have is_deleted=True"
                print("  - Verified: Item appears as deleted in list")


class TestAdminLayoutCopy:
    """Test POST /api/admin/layouts/{revision_id}/copy"""
    
    def test_copy_nonexistent(self, auth_headers):
        """Test copy with nonexistent revision_id"""
        fake_uuid = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{fake_uuid}/copy",
            headers=auth_headers,
            json={
                "target_page_type": "home",
                "country": "TR",
                "module": "vehicle"
            }
        )
        assert response.status_code == 404, f"Expected 404 for nonexistent, got {response.status_code}"
        print("SUCCESS: Nonexistent revision returns 404 for copy")
    
    def test_copy_invalid_uuid(self, auth_headers):
        """Test copy with invalid UUID"""
        response = requests.post(
            f"{BASE_URL}/api/admin/layouts/invalid-uuid/copy",
            headers=auth_headers,
            json={
                "target_page_type": "home",
                "country": "TR",
                "module": "vehicle"
            }
        )
        assert response.status_code == 400, f"Expected 400 for invalid UUID, got {response.status_code}"
        print("SUCCESS: Invalid UUID returns 400 for copy")
    
    def test_copy_missing_required_fields(self, auth_headers):
        """Test copy with missing required fields"""
        fake_uuid = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{fake_uuid}/copy",
            headers=auth_headers,
            json={}  # Missing required fields
        )
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        print("SUCCESS: Missing fields returns 422")
    
    def test_copy_existing_revision(self, auth_headers):
        """Test copy on an existing revision"""
        # First, get a revision from the list
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"statuses": "draft,published", "limit": 10}
        )
        
        if list_response.status_code != 200 or not list_response.json().get("items"):
            pytest.skip("No revisions available to test copy")
        
        source_item = None
        for item in list_response.json()["items"]:
            if not item.get("is_deleted"):
                source_item = item
                break
        
        if not source_item:
            pytest.skip("No non-deleted revision available for copy test")
        
        revision_id = source_item.get("revision_id") or source_item.get("id")
        
        # Perform copy with unique target scope
        test_module = f"test_copy_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/copy",
            headers=auth_headers,
            json={
                "target_page_type": "home",
                "country": "TR",
                "module": test_module,
                "category_id": None,
                "publish_after_copy": False
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "target_page" in data or "target_revision" in data, "Response should have target_page or target_revision"
        
        target = data.get("target_page") or data.get("target_revision") or {}
        print(f"SUCCESS: Copy created - target page type: {target.get('page_type', 'N/A')}")
        print(f"  - Target module: {test_module}")


class TestAdminLayoutRevisionsForPage:
    """Test GET /api/admin/site/content-layout/pages/{page_id}/revisions"""
    
    def test_list_revisions_for_page(self, auth_headers):
        """Test listing revisions for a specific page"""
        # First get a page ID from layouts list
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"statuses": "draft,published", "limit": 5}
        )
        
        if list_response.status_code != 200 or not list_response.json().get("items"):
            pytest.skip("No layouts available to test revisions")
        
        page_id = list_response.json()["items"][0].get("layout_page_id")
        if not page_id:
            pytest.skip("No layout_page_id found in list items")
        
        # Get revisions for that page
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should have items array"
        
        if data["items"]:
            revision = data["items"][0]
            assert "id" in revision, "Revision should have id"
            assert "status" in revision, "Revision should have status"
            assert "version" in revision, "Revision should have version"
        
        print(f"SUCCESS: Revisions for page {page_id} - count: {len(data['items'])}")


class TestContentListColumns:
    """Test that list returns all expected columns for Content List table"""
    
    def test_content_list_columns(self, auth_headers):
        """Verify all required columns are present in response"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"statuses": "draft,published", "limit": 5}
        )
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No items to verify columns")
        
        item = items[0]
        
        # Required columns for Content List table:
        required_columns = [
            "page_type",     # Sayfa Tipi
            "country",       # Ülke
            "module",        # Modül
            "scope",         # category_id/scope
            "status",        # Status
            "version",       # Version
            "updated_at",    # updated_at
            "is_deleted"     # Deleted status (for red styling)
        ]
        
        for col in required_columns:
            # category_id can substitute for scope
            if col == "scope" and "scope" not in item and "category_id" in item:
                continue
            assert col in item, f"Missing required column: {col}"
        
        print(f"SUCCESS: All required columns present in response")
        print(f"  - Columns: {list(item.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
