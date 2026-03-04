"""
Apple Sign-In System Settings Tests - Iteration 116
Tests:
- GET /api/admin/system-settings/apple-signin: Retrieve current Apple Sign-In config
- POST /api/admin/system-settings/apple-signin: Save team_id, client_id, key_id, private_key
- clear_private_key scenario: Clears existing private_key
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Login as admin and get access token"""
    url = f"{BASE_URL}/api/auth/login"
    payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    response = requests.post(url, json=payload, timeout=15)
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    token = data.get("access_token")
    assert token, "No access_token in login response"
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Build auth headers"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestAppleSignInGetEndpoint:
    """GET /api/admin/system-settings/apple-signin tests"""

    def test_get_apple_signin_endpoint_exists(self, auth_headers):
        """Verify the GET endpoint exists and returns 200"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        response = requests.get(url, headers=auth_headers, timeout=15)
        assert response.status_code == 200, f"GET apple-signin failed: {response.text}"
        data = response.json()
        # Check response structure
        assert "configured" in data, "Missing 'configured' field"
        assert "team_id_masked" in data, "Missing 'team_id_masked' field"
        assert "client_id_masked" in data, "Missing 'client_id_masked' field"
        assert "key_id_masked" in data, "Missing 'key_id_masked' field"
        assert "private_key_masked" in data, "Missing 'private_key_masked' field"
        assert "key" in data, "Missing 'key' field"
        assert data["key"] == "integrations.apple_signin.credentials"
        print(f"GET apple-signin response: {data}")

    def test_get_apple_signin_unauthenticated(self):
        """Verify the endpoint rejects unauthenticated requests"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        response = requests.get(url, timeout=15)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestAppleSignInPostEndpoint:
    """POST /api/admin/system-settings/apple-signin tests"""

    def test_post_apple_signin_endpoint_exists(self, auth_headers):
        """Verify the POST endpoint exists"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        payload = {}  # Empty payload to just test endpoint existence
        response = requests.post(url, json=payload, headers=auth_headers, timeout=15)
        # Should not return 404 or 405
        assert response.status_code not in [404, 405], f"POST endpoint not found: {response.status_code}"
        print(f"POST apple-signin status: {response.status_code}")

    def test_post_apple_signin_save_credentials(self, auth_headers):
        """Save Apple Sign-In credentials (team_id, client_id, key_id, private_key)"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        test_team_id = "TEST_TEAM_ID_12345"
        test_client_id = "com.test.webservices"
        test_key_id = "TEST_KEY_ID_ABC"
        test_private_key = "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY_CONTENT\n-----END PRIVATE KEY-----"

        payload = {
            "team_id": test_team_id,
            "client_id": test_client_id,
            "key_id": test_key_id,
            "private_key": test_private_key,
        }
        response = requests.post(url, json=payload, headers=auth_headers, timeout=15)
        assert response.status_code == 200, f"POST apple-signin failed: {response.text}"
        data = response.json()
        assert "configured" in data, "Missing 'configured' in response"
        assert data["configured"] is True, "Expected 'configured' to be True after saving all credentials"
        assert "team_id_masked" in data, "Missing 'team_id_masked'"
        assert "client_id_masked" in data, "Missing 'client_id_masked'"
        assert "key_id_masked" in data, "Missing 'key_id_masked'"
        assert "private_key_masked" in data, "Missing 'private_key_masked'"
        # Verify masked values are not empty
        assert data["team_id_masked"], "team_id_masked should not be empty"
        assert data["client_id_masked"], "client_id_masked should not be empty"
        assert data["key_id_masked"], "key_id_masked should not be empty"
        assert data["private_key_masked"], "private_key_masked should not be empty"
        print(f"POST apple-signin save response: {data}")

    def test_post_apple_signin_get_after_save(self, auth_headers):
        """Verify GET returns saved credentials after POST"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        response = requests.get(url, headers=auth_headers, timeout=15)
        assert response.status_code == 200, f"GET failed: {response.text}"
        data = response.json()
        # After saving all fields, 'configured' should be True
        assert data["configured"] is True, "Expected 'configured' to be True"
        assert data["team_id_masked"], "team_id_masked should not be empty"
        assert data["client_id_masked"], "client_id_masked should not be empty"
        assert data["key_id_masked"], "key_id_masked should not be empty"
        assert data["private_key_masked"], "private_key_masked should not be empty"

    def test_post_apple_signin_partial_update(self, auth_headers):
        """Test partial update - only update team_id"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        payload = {
            "team_id": "UPDATED_TEAM_ID_678",
        }
        response = requests.post(url, json=payload, headers=auth_headers, timeout=15)
        assert response.status_code == 200, f"Partial update failed: {response.text}"
        data = response.json()
        # Should still be configured because we preserve existing values
        assert data["configured"] is True, "Expected 'configured' to be True after partial update"
        print(f"Partial update response: {data}")


class TestAppleSignInClearPrivateKey:
    """Test clear_private_key scenario"""

    def test_clear_private_key(self, auth_headers):
        """Test clearing private_key while preserving other fields"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        
        # First, ensure we have all credentials set
        setup_payload = {
            "team_id": "CLEAR_TEST_TEAM",
            "client_id": "com.clear.test",
            "key_id": "CLEAR_KEY_ID",
            "private_key": "-----BEGIN PRIVATE KEY-----\nCLEAR_TEST_KEY\n-----END PRIVATE KEY-----",
        }
        setup_response = requests.post(url, json=setup_payload, headers=auth_headers, timeout=15)
        assert setup_response.status_code == 200, f"Setup failed: {setup_response.text}"
        assert setup_response.json()["configured"] is True, "Setup should result in configured=True"
        
        # Now clear the private key
        clear_payload = {
            "clear_private_key": True,
        }
        response = requests.post(url, json=clear_payload, headers=auth_headers, timeout=15)
        assert response.status_code == 200, f"Clear private key failed: {response.text}"
        data = response.json()
        # After clearing private_key, 'configured' should be False
        assert data["configured"] is False, "Expected 'configured' to be False after clearing private_key"
        # Other fields should still be masked (non-empty)
        assert data["team_id_masked"], "team_id_masked should still be present"
        assert data["client_id_masked"], "client_id_masked should still be present"
        assert data["key_id_masked"], "key_id_masked should still be present"
        # private_key_masked should be empty after clear
        assert data["private_key_masked"] == "", "private_key_masked should be empty after clear"
        print(f"Clear private key response: {data}")

    def test_get_after_clear_private_key(self, auth_headers):
        """Verify GET returns correct state after private_key is cleared"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        response = requests.get(url, headers=auth_headers, timeout=15)
        assert response.status_code == 200, f"GET failed: {response.text}"
        data = response.json()
        # After clearing, configured should be False
        assert data["configured"] is False, "Expected 'configured' to be False after clearing"
        print(f"GET after clear response: {data}")


class TestAppleSignInAuthorization:
    """Test authorization scenarios"""

    def test_post_unauthenticated(self):
        """Verify POST rejects unauthenticated requests"""
        url = f"{BASE_URL}/api/admin/system-settings/apple-signin"
        payload = {"team_id": "UNAUTHORIZED_TEAM"}
        response = requests.post(url, json=payload, timeout=15)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
