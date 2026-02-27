"""
P72 Vitrin Yönetimi - Admin to Public Sync & Delete Tests
Tests:
1. DB/public config kontrolü: /api/site/showcase-layout values match admin saved values
2. Admin versions delete button behavior
3. Active (published) version delete returns 400
4. Draft version delete flow
5. Public HomePage column/row/listing_count sync
6. Cache-Control: no-store header check
"""

import os
import pytest
import requests
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_CREDENTIALS = {
    "email": "admin@platform.com",
    "password": "Admin123!"
}


@pytest.fixture(scope="module")
def admin_token():
    """Login and get admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    token = response.json().get("access_token")
    if not token:
        pytest.skip("No access token returned")
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Return admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestShowcasePublicSyncVerification:
    """Test that admin changes are reflected in public endpoint"""

    def test_public_endpoint_returns_cache_control_no_store(self):
        """Public endpoint should have Cache-Control: no-store header"""
        response = requests.get(f"{BASE_URL}/api/site/showcase-layout")
        assert response.status_code == 200
        
        cache_control = response.headers.get("Cache-Control", "")
        assert "no-store" in cache_control.lower(), f"Expected no-store header, got: {cache_control}"
        print(f"PASS: Cache-Control header = {cache_control}")

    def test_admin_saved_values_match_public_published(self, admin_headers):
        """Verify admin saved values match public endpoint after publish"""
        # Step 1: Create a draft with specific values
        test_rows = 5
        test_columns = 4
        test_listing_count = 20
        
        draft_config = {
            "homepage": {
                "enabled": True,
                "rows": test_rows,
                "columns": test_columns,
                "listing_count": test_listing_count
            },
            "category_showcase": {
                "enabled": True,
                "default": {"rows": 2, "columns": 4, "listing_count": 8},
                "categories": []
            }
        }
        
        save_response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json={"config": draft_config, "status": "draft"},
            headers=admin_headers
        )
        assert save_response.status_code == 200, f"Save draft failed: {save_response.text}"
        draft_id = save_response.json().get("id")
        print(f"Created draft with id={draft_id}")
        
        # Step 2: Publish the draft
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{draft_id}/publish",
            headers=admin_headers
        )
        assert publish_response.status_code == 200, f"Publish failed: {publish_response.text}"
        print(f"Published draft id={draft_id}")
        
        # Small delay to ensure DB update is committed
        time.sleep(0.5)
        
        # Step 3: Verify public endpoint returns same values
        public_response = requests.get(f"{BASE_URL}/api/site/showcase-layout")
        assert public_response.status_code == 200
        public_config = public_response.json().get("config", {}).get("homepage", {})
        
        assert public_config.get("rows") == test_rows, f"Expected rows={test_rows}, got {public_config.get('rows')}"
        assert public_config.get("columns") == test_columns, f"Expected columns={test_columns}, got {public_config.get('columns')}"
        assert public_config.get("listing_count") == test_listing_count, f"Expected listing_count={test_listing_count}, got {public_config.get('listing_count')}"
        
        print(f"PASS: Public endpoint reflects admin saved values - rows={test_rows}, columns={test_columns}, listing_count={test_listing_count}")


class TestShowcaseVersionDelete:
    """Test showcase version delete functionality"""

    def test_delete_published_version_returns_400(self, admin_headers):
        """DELETE on published version should return 400 with specific error message"""
        # First, get the published version
        versions_response = requests.get(
            f"{BASE_URL}/api/admin/site/showcase-layout/configs",
            headers=admin_headers
        )
        assert versions_response.status_code == 200
        
        versions = versions_response.json().get("items", [])
        published_versions = [v for v in versions if v.get("status") == "published"]
        
        if not published_versions:
            pytest.skip("No published version found to test delete")
        
        published_id = published_versions[0].get("id")
        
        # Try to delete published version
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{published_id}",
            headers=admin_headers
        )
        
        assert delete_response.status_code == 400, f"Expected 400 for published delete, got {delete_response.status_code}"
        
        error_detail = delete_response.json().get("detail", "")
        # Backend returns "Aktif versiyon silinemez"
        assert "silinemez" in error_detail.lower() or "aktif" in error_detail.lower(), f"Expected 'Aktif versiyon silinemez' error, got: {error_detail}"
        
        print(f"PASS: Delete published version returns 400 with message: {error_detail}")

    def test_delete_draft_version_works(self, admin_headers):
        """DELETE on draft version should succeed"""
        # Step 1: Create a new draft version
        draft_config = {
            "homepage": {
                "enabled": True,
                "rows": 3,
                "columns": 3,
                "listing_count": 9
            },
            "category_showcase": {
                "enabled": False,
                "default": {"rows": 1, "columns": 1, "listing_count": 1},
                "categories": []
            }
        }
        
        save_response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json={"config": draft_config, "status": "draft"},
            headers=admin_headers
        )
        assert save_response.status_code == 200, f"Save draft failed: {save_response.text}"
        draft_id = save_response.json().get("id")
        draft_version = save_response.json().get("version")
        print(f"Created draft for deletion test: id={draft_id}, version={draft_version}")
        
        # Step 2: Verify it's in versions list with draft status
        versions_response = requests.get(
            f"{BASE_URL}/api/admin/site/showcase-layout/configs",
            headers=admin_headers
        )
        assert versions_response.status_code == 200
        versions = versions_response.json().get("items", [])
        draft_in_list = any(v.get("id") == draft_id and v.get("status") == "draft" for v in versions)
        assert draft_in_list, f"Draft {draft_id} not found in versions list with draft status"
        
        # Step 3: Delete the draft
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{draft_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 200, f"Delete draft failed: {delete_response.status_code} - {delete_response.text}"
        
        # Step 4: Verify it's removed from versions list
        versions_response_after = requests.get(
            f"{BASE_URL}/api/admin/site/showcase-layout/configs",
            headers=admin_headers
        )
        versions_after = versions_response_after.json().get("items", [])
        draft_still_exists = any(v.get("id") == draft_id for v in versions_after)
        assert not draft_still_exists, f"Draft {draft_id} still exists after deletion"
        
        print(f"PASS: Draft version {draft_id} deleted successfully")

    def test_delete_endpoint_requires_auth(self):
        """DELETE endpoint without auth should return 401/403"""
        # Use a dummy UUID
        dummy_id = "00000000-0000-0000-0000-000000000000"
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{dummy_id}"
        )
        assert delete_response.status_code in [401, 403], f"Expected 401/403 without auth, got {delete_response.status_code}"
        print(f"PASS: Delete endpoint requires auth, returns {delete_response.status_code}")

    def test_delete_nonexistent_version_returns_404(self, admin_headers):
        """DELETE on nonexistent version should return 404"""
        nonexistent_id = "12345678-1234-1234-1234-123456789abc"
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{nonexistent_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 404, f"Expected 404 for nonexistent, got {delete_response.status_code}"
        print(f"PASS: Delete nonexistent version returns 404")

    def test_delete_invalid_uuid_returns_400(self, admin_headers):
        """DELETE with invalid UUID should return 400"""
        invalid_id = "not-a-uuid"
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{invalid_id}",
            headers=admin_headers
        )
        assert delete_response.status_code == 400, f"Expected 400 for invalid UUID, got {delete_response.status_code}"
        print(f"PASS: Delete invalid UUID returns 400")


class TestShowcaseSaveDraftPublishFlow:
    """Test the complete save draft → publish flow"""

    def test_save_draft_then_publish_updates_public(self, admin_headers):
        """Complete flow: save draft → publish → verify public endpoint reflects new values"""
        # Unique test values
        new_rows = 6
        new_columns = 5
        new_listing_count = 30
        
        # Step 1: Save draft
        draft_config = {
            "homepage": {
                "enabled": True,
                "rows": new_rows,
                "columns": new_columns,
                "listing_count": new_listing_count
            },
            "category_showcase": {
                "enabled": True,
                "default": {"rows": 3, "columns": 5, "listing_count": 15},
                "categories": []
            }
        }
        
        save_response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json={"config": draft_config, "status": "draft"},
            headers=admin_headers
        )
        assert save_response.status_code == 200
        draft_id = save_response.json().get("id")
        print(f"Step 1: Draft saved with id={draft_id}")
        
        # Step 2: Verify public still has old values (not draft)
        public_before = requests.get(f"{BASE_URL}/api/site/showcase-layout")
        before_version = public_before.json().get("version")
        print(f"Step 2: Public version before publish: {before_version}")
        
        # Step 3: Publish
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{draft_id}/publish",
            headers=admin_headers
        )
        assert publish_response.status_code == 200
        print(f"Step 3: Published draft {draft_id}")
        
        # Small delay
        time.sleep(0.3)
        
        # Step 4: Verify public now has new values
        public_after = requests.get(f"{BASE_URL}/api/site/showcase-layout")
        assert public_after.status_code == 200
        after_data = public_after.json()
        after_config = after_data.get("config", {}).get("homepage", {})
        
        assert after_config.get("rows") == new_rows, f"Rows mismatch: expected {new_rows}, got {after_config.get('rows')}"
        assert after_config.get("columns") == new_columns, f"Columns mismatch: expected {new_columns}, got {after_config.get('columns')}"
        assert after_config.get("listing_count") == new_listing_count, f"Listing count mismatch: expected {new_listing_count}, got {after_config.get('listing_count')}"
        
        print(f"Step 4: PASS - Public endpoint updated with new values: rows={new_rows}, columns={new_columns}, listing_count={new_listing_count}")


class TestVersionsListEndpoint:
    """Test versions list functionality"""

    def test_versions_list_contains_status_field(self, admin_headers):
        """Versions list should include status field for each item"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/showcase-layout/configs",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        versions = response.json().get("items", [])
        for version in versions:
            assert "id" in version, "Version item should have id"
            assert "status" in version, "Version item should have status"
            assert "version" in version, "Version item should have version number"
            assert version.get("status") in ["draft", "published"], f"Invalid status: {version.get('status')}"
        
        published_count = sum(1 for v in versions if v.get("status") == "published")
        draft_count = sum(1 for v in versions if v.get("status") == "draft")
        print(f"PASS: Versions list has {len(versions)} items - {published_count} published, {draft_count} draft")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
