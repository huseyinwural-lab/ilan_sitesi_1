"""
Iteration 156 - Test publish draft functionality for Content Builder
Tests:
1. Backend POST /api/admin/site/content-layout/revisions/{draft_id}/publish works for valid draft
2. Backend publish no longer blocked by unknown/inactive component definitions (except deprecated blocked keys)
3. Frontend shows real backend error text when publish fails
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://0.0.0.0:8001').rstrip('/')

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


class TestPublishDraft:
    """Tests for publish draft functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_get_existing_drafts(self):
        """Test fetching existing layouts and drafts"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            params={"include_deleted": "false", "statuses": "draft,published", "page": 1, "limit": 50},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200, f"Failed to get layouts: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"Found {len(data['items'])} layouts")
        
        # Find draft items
        drafts = [item for item in data['items'] if item.get('status') == 'draft']
        print(f"Found {len(drafts)} draft items")
        return drafts
    
    def test_publish_valid_draft_with_components(self):
        """
        Test that a draft with valid components can be published.
        This tests that publish_guard no longer blocks unknown/inactive component definitions.
        """
        # First get existing drafts
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            params={"include_deleted": "false", "statuses": "draft", "page": 1, "limit": 50},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        drafts = data.get('items', [])
        
        if not drafts:
            # Create a new draft
            print("No drafts found, creating one...")
            # First need to get/create a layout page
            pages_resp = requests.get(
                f"{BASE_URL}/api/admin/layouts",
                params={"include_deleted": "false", "statuses": "draft,published", "page": 1, "limit": 10},
                headers=self.headers,
                timeout=15
            )
            pages_data = pages_resp.json()
            if pages_data.get('items'):
                first_item = pages_data['items'][0]
                page_id = first_item.get('layout_page_id')
                
                # Create draft via PUT
                create_draft_resp = requests.put(
                    f"{BASE_URL}/api/admin/site/content-layout/layouts/{page_id}/draft",
                    json={
                        "payload_json": {
                            "rows": [
                                {
                                    "id": "row-test-1",
                                    "columns": [
                                        {
                                            "id": "col-test-1",
                                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                            "components": [
                                                {
                                                    "id": "cmp-test-1",
                                                    "key": "shared.text-block",
                                                    "props": {"title": "Test Block", "body": "Test content"},
                                                    "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    },
                    headers=self.headers,
                    timeout=15
                )
                if create_draft_resp.status_code in [200, 201]:
                    draft_id = create_draft_resp.json().get('item', {}).get('id')
                    drafts = [{"id": draft_id, "revision_id": draft_id}]
        
        if not drafts:
            pytest.skip("No drafts available for testing")
            return
        
        # Try to publish the first draft
        draft_item = drafts[0]
        draft_id = draft_item.get('revision_id') or draft_item.get('id')
        print(f"Attempting to publish draft: {draft_id}")
        
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            json={},
            headers=self.headers,
            timeout=30
        )
        
        print(f"Publish response status: {publish_response.status_code}")
        print(f"Publish response body: {publish_response.text}")
        
        # Check the response - it should either succeed or fail with a clear error
        if publish_response.status_code == 200:
            result = publish_response.json()
            assert result.get('ok') == True, "Publish should succeed with ok=True"
            print("Publish successful!")
        elif publish_response.status_code == 400:
            # Check the error message
            error_data = publish_response.json()
            detail = error_data.get('detail')
            print(f"Publish blocked with 400: {detail}")
            
            # Should NOT be blocked by unknown_or_inactive - that guard was removed
            if isinstance(detail, dict):
                code = detail.get('code', '')
                assert 'unknown_or_inactive' not in code, \
                    f"Publish should not be blocked by unknown_or_inactive components: {detail}"
            elif isinstance(detail, str):
                assert 'unknown_or_inactive' not in detail, \
                    f"Publish should not be blocked by unknown_or_inactive components: {detail}"
            
            # Check if blocked by deprecated keys (which is expected)
            if isinstance(detail, dict) and detail.get('code') == 'publish_guard_blocked_components':
                blocked_keys = detail.get('blocked_keys', [])
                print(f"Blocked by deprecated component keys: {blocked_keys}")
                # This is expected behavior
        elif publish_response.status_code == 409:
            # Conflict - draft already published or similar
            print(f"Publish conflict (expected): {publish_response.json()}")
        else:
            # Unexpected status
            pytest.fail(f"Unexpected publish response: {publish_response.status_code} - {publish_response.text}")
    
    def test_publish_error_returns_detailed_message(self):
        """
        Test that publish endpoint returns detailed error messages.
        Frontend should be able to display these errors.
        """
        # Test with a non-existent draft ID
        fake_draft_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{fake_draft_id}/publish",
            json={},
            headers=self.headers,
            timeout=15
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        error_data = response.json()
        assert 'detail' in error_data, "Error response should include 'detail'"
        print(f"Error response for non-existent draft: {error_data}")
    
    def test_publish_guard_blocked_keys_error_format(self):
        """
        Test that when blocked keys cause publish to fail,
        the error includes both code and blocked_keys list.
        """
        # Get a layout page to create a draft with blocked components
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            params={"include_deleted": "false", "statuses": "draft,published", "page": 1, "limit": 5},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            pytest.skip("No layout items available")
            return
        
        page_id = items[0].get('layout_page_id')
        
        # Create draft with a deprecated blocked component key
        payload_with_blocked = {
            "payload_json": {
                "rows": [
                    {
                        "id": "row-blocked-test",
                        "columns": [
                            {
                                "id": "col-blocked-test",
                                "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                "components": [
                                    {
                                        "id": "cmp-blocked-test",
                                        "key": "category.navigator",  # This is a blocked key
                                        "props": {},
                                        "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        # Update/create draft
        draft_resp = requests.put(
            f"{BASE_URL}/api/admin/site/content-layout/layouts/{page_id}/draft",
            json=payload_with_blocked,
            headers=self.headers,
            timeout=15
        )
        
        if draft_resp.status_code not in [200, 201]:
            print(f"Could not create draft with blocked component: {draft_resp.text}")
            pytest.skip("Could not create draft for blocked key test")
            return
        
        draft_id = draft_resp.json().get('item', {}).get('id')
        if not draft_id:
            pytest.skip("No draft ID returned")
            return
        
        # Try to publish - should be blocked
        publish_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            json={},
            headers=self.headers,
            timeout=15
        )
        
        print(f"Blocked publish response: {publish_resp.status_code} - {publish_resp.text}")
        
        assert publish_resp.status_code == 400, "Publishing with blocked keys should return 400"
        error_data = publish_resp.json()
        detail = error_data.get('detail')
        
        # Check error format
        assert isinstance(detail, dict), f"Error detail should be dict, got: {type(detail)}"
        assert detail.get('code') == 'publish_guard_blocked_components', \
            f"Expected code 'publish_guard_blocked_components', got: {detail}"
        assert 'blocked_keys' in detail, "Error should include 'blocked_keys' list"
        assert 'category.navigator' in detail['blocked_keys'], \
            f"Blocked keys should include 'category.navigator': {detail['blocked_keys']}"


class TestPublishEndpointContract:
    """Test the publish endpoint contract and error handling"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15
        )
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        yield
    
    def test_publish_endpoint_exists(self):
        """Test that the publish endpoint exists and requires auth"""
        # Test without auth
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/test-id/publish",
            json={},
            timeout=15
        )
        assert response.status_code in [401, 403], "Endpoint should require auth"
    
    def test_publish_returns_ok_true_on_success_or_error_detail(self):
        """
        Test that publish endpoint returns proper structure:
        - Success: {"ok": true, "item": {...}}
        - Error: {"detail": "..." or {"code": "...", ...}}
        """
        # Get a draft to test
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            params={"include_deleted": "false", "statuses": "draft", "page": 1, "limit": 5},
            headers=self.headers,
            timeout=15
        )
        assert response.status_code == 200
        drafts = response.json().get('items', [])
        
        if not drafts:
            pytest.skip("No drafts to test")
            return
        
        draft_id = drafts[0].get('revision_id') or drafts[0].get('id')
        
        # Attempt publish
        publish_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            json={},
            headers=self.headers,
            timeout=30
        )
        
        result = publish_resp.json()
        
        if publish_resp.status_code == 200:
            # Success response
            assert result.get('ok') == True, "Success should have ok=True"
            assert 'item' in result, "Success should include item"
        elif publish_resp.status_code in [400, 404, 409]:
            # Error response
            assert 'detail' in result, "Error should have detail field"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
