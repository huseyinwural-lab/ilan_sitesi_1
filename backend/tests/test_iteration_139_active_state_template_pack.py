"""
Iteration 139: Test active/passive state toggle + template pack install/verify features

Test Coverage:
- PATCH /api/admin/layouts/{revision_id}/active - toggle is_active true/false
- GET /api/admin/layouts - verify is_active field in list response
- DELETE /api/admin/layouts/{revision_id} - verify is_active=false after soft-delete
- POST /api/admin/site/content-layout/preset/install-standard-pack - install TR,DE,FR templates
- GET /api/admin/site/content-layout/preset/verify-standard-pack - verify publish matrix
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestLayoutActiveStateAndTemplatePack:
    """Test layout active state toggle and template pack installation/verification"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip("Admin authentication failed")
        return response.json().get("access_token")

    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Create authorization headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    def test_01_list_layouts_returns_is_active_field(self, auth_headers):
        """GET /api/admin/layouts should return is_active field for each item"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": "true", "statuses": "draft,published", "limit": 50},
            timeout=30,
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "items" in data, "Response should have items field"
        
        # If items exist, verify is_active field is present
        if data["items"]:
            first_item = data["items"][0]
            assert "is_active" in first_item, f"is_active field should be in list response: {first_item.keys()}"
            assert isinstance(first_item["is_active"], bool), "is_active should be boolean"
            print(f"PASS: is_active field present in list response. First item is_active={first_item['is_active']}")
        else:
            print("PASS: List endpoint returned 200 (no items to verify is_active field)")

    def test_02_toggle_revision_active_to_false(self, auth_headers):
        """PATCH /api/admin/layouts/{revision_id}/active should set is_active=false"""
        # First, get a layout that is not deleted
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": "false", "statuses": "draft,published", "limit": 50},
            timeout=30,
        )
        
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        
        # Find an active, non-deleted revision
        target_item = None
        for item in items:
            if not item.get("is_deleted", False) and item.get("is_active", False):
                target_item = item
                break
        
        if not target_item:
            # Try to find any non-deleted item
            for item in items:
                if not item.get("is_deleted", False):
                    target_item = item
                    break
        
        if not target_item:
            pytest.skip("No non-deleted layout revision found for testing")
        
        revision_id = target_item["revision_id"]
        
        # Toggle to false
        patch_response = requests.patch(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
            headers=auth_headers,
            json={"is_active": False},
            timeout=30,
        )
        
        assert patch_response.status_code == 200, f"Expected 200, got {patch_response.status_code}: {patch_response.text}"
        data = patch_response.json()
        
        assert data.get("ok") is True, "Response should have ok=true"
        assert "item" in data, "Response should have item"
        assert data["item"]["is_active"] is False, "is_active should be false after toggle"
        print(f"PASS: Toggled revision {revision_id} to is_active=false")
        
        # Toggle back to true
        restore_response = requests.patch(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
            headers=auth_headers,
            json={"is_active": True},
            timeout=30,
        )
        
        assert restore_response.status_code == 200
        assert restore_response.json()["item"]["is_active"] is True
        print(f"PASS: Restored revision {revision_id} to is_active=true")

    def test_03_toggle_active_to_true(self, auth_headers):
        """PATCH /api/admin/layouts/{revision_id}/active should set is_active=true"""
        # Get a list and find an inactive but not deleted item
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": "false", "statuses": "draft,published", "limit": 50},
            timeout=30,
        )
        
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        
        if not items:
            pytest.skip("No layouts found for testing")
        
        # Use first non-deleted item, toggle it
        target_item = None
        for item in items:
            if not item.get("is_deleted", False):
                target_item = item
                break
        
        if not target_item:
            pytest.skip("No non-deleted layout revision found")
        
        revision_id = target_item["revision_id"]
        
        # Toggle to true (ensures it's true)
        response = requests.patch(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
            headers=auth_headers,
            json={"is_active": True},
            timeout=30,
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("ok") is True
        assert data["item"]["is_active"] is True
        print(f"PASS: Set revision {revision_id} to is_active=true")

    def test_04_toggle_deleted_revision_returns_error(self, auth_headers):
        """PATCH /api/admin/layouts/{revision_id}/active on deleted revision should return 400"""
        # Get deleted items
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": "true", "statuses": "draft,published", "limit": 200},
            timeout=30,
        )
        
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        
        # Find a deleted item
        deleted_item = None
        for item in items:
            if item.get("is_deleted", False):
                deleted_item = item
                break
        
        if not deleted_item:
            pytest.skip("No deleted layout revision found for testing")
        
        revision_id = deleted_item["revision_id"]
        
        # Try to toggle - should fail with 400
        response = requests.patch(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/active",
            headers=auth_headers,
            json={"is_active": True},
            timeout=30,
        )
        
        assert response.status_code == 400, f"Expected 400 for deleted revision, got {response.status_code}"
        print(f"PASS: Correctly rejected active toggle on deleted revision {revision_id}")

    def test_05_soft_delete_sets_is_active_false(self, auth_headers):
        """DELETE /api/admin/layouts/{revision_id} should set is_active=false"""
        # First create or find a test layout we can delete
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={"include_deleted": "false", "statuses": "draft", "limit": 50},
            timeout=30,
        )
        
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        
        # Find a draft item to delete (we don't want to delete important published items)
        draft_item = None
        for item in items:
            if item.get("status") == "draft" and not item.get("is_deleted", False):
                draft_item = item
                break
        
        if not draft_item:
            pytest.skip("No draft layout revision found for delete test")
        
        revision_id = draft_item["revision_id"]
        initial_active = draft_item.get("is_active", True)
        print(f"Found draft revision {revision_id} with is_active={initial_active}")
        
        # Delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/layouts/{revision_id}",
            headers=auth_headers,
            timeout=30,
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        data = delete_response.json()
        
        assert data.get("ok") is True
        assert data["item"]["is_deleted"] is True, "is_deleted should be true after soft-delete"
        assert data["item"]["is_active"] is False, "is_active should be false after soft-delete"
        print(f"PASS: Soft-delete set is_deleted=true and is_active=false for revision {revision_id}")

    def test_06_install_standard_template_pack(self, auth_headers):
        """POST /api/admin/site/content-layout/preset/install-standard-pack should work for TR,DE,FR"""
        payload = {
            "countries": ["TR", "DE", "FR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": True,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json=payload,
            timeout=120,  # Template pack install can take time
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("ok") is True, "Response should have ok=true"
        assert "summary" in data, "Response should have summary"
        assert "results" in data, "Response should have results"
        assert data.get("countries") == ["TR", "DE", "FR"], "Countries should match request"
        assert data.get("module") == "global", "Module should match request"
        
        summary = data["summary"]
        assert "created_pages" in summary, "Summary should have created_pages"
        assert "updated_drafts" in summary, "Summary should have updated_drafts"
        assert "published_revisions" in summary, "Summary should have published_revisions"
        
        print(f"PASS: Install standard pack completed. Summary: {summary}")

    def test_07_verify_standard_template_pack(self, auth_headers):
        """GET /api/admin/site/content-layout/preset/verify-standard-pack should return matrix"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers=auth_headers,
            params={
                "countries": "TR,DE,FR",
                "module": "global",
            },
            timeout=60,
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("ok") is True, "Response should have ok=true"
        assert "summary" in data, "Response should have summary"
        assert "items" in data, "Response should have items (matrix)"
        
        summary = data["summary"]
        assert "ready_rows" in summary, "Summary should have ready_rows"
        assert "total_rows" in summary, "Summary should have total_rows"
        assert "ready_ratio" in summary, "Summary should have ready_ratio"
        
        # Verify items contain expected fields
        if data["items"]:
            first_item = data["items"][0]
            expected_fields = ["country", "module", "page_type", "layout_page_id", "published_revision_id", "published_revision_active", "is_ready"]
            for field in expected_fields:
                assert field in first_item, f"Item should have field: {field}"
        
        print(f"PASS: Verify standard pack returned matrix. Summary: {summary}")

    def test_08_verify_pack_returns_ready_ratio(self, auth_headers):
        """GET /api/admin/site/content-layout/preset/verify-standard-pack should return valid ready_ratio"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers=auth_headers,
            params={
                "countries": "TR,DE,FR",
                "module": "global",
            },
            timeout=60,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("summary", {})
        ready_ratio = summary.get("ready_ratio", 0)
        ready_rows = summary.get("ready_rows", 0)
        total_rows = summary.get("total_rows", 0)
        
        assert isinstance(ready_ratio, (int, float)), "ready_ratio should be a number"
        assert 0 <= ready_ratio <= 100, "ready_ratio should be between 0 and 100"
        assert total_rows > 0, "total_rows should be > 0 for TR,DE,FR"
        
        print(f"PASS: ready_ratio={ready_ratio}% ({ready_rows}/{total_rows} rows ready)")

    def test_09_install_pack_single_country(self, auth_headers):
        """POST /api/admin/site/content-layout/preset/install-standard-pack should work for single country"""
        payload = {
            "countries": ["TR"],
            "module": "vehicle",
            "persona": "corporate",
            "variant": "B",
            "overwrite_existing_draft": False,
            "publish_after_seed": False,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json=payload,
            timeout=120,
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data.get("ok") is True
        assert data.get("persona") == "corporate", "Persona should match request"
        assert data.get("variant") == "B", "Variant should match request"
        
        print(f"PASS: Install pack for single country (TR/vehicle/corporate/B) completed")

    def test_10_verify_invalid_country_returns_400(self, auth_headers):
        """GET /api/admin/site/content-layout/preset/verify-standard-pack with invalid country should fail"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers=auth_headers,
            params={
                "countries": "X",  # Too short, invalid
                "module": "global",
            },
            timeout=30,
        )
        
        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
        print(f"PASS: Invalid country correctly rejected with status {response.status_code}")

    def test_11_install_pack_empty_countries_returns_400(self, auth_headers):
        """POST /api/admin/site/content-layout/preset/install-standard-pack with empty countries should fail"""
        payload = {
            "countries": [],
            "module": "global",
            "persona": "individual",
            "variant": "A",
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers=auth_headers,
            json=payload,
            timeout=30,
        )
        
        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
        print(f"PASS: Empty countries correctly rejected with status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
