"""
P1 Dealer Settings Tests - Testing:
- /api/dealer/settings/profile (GET, PATCH)
- /api/dealer/settings/change-password (POST) 
- /api/dealer/settings/preferences (GET, PATCH)
- /api/dealer/settings/blocked-accounts (POST, DELETE)

Iteration 41 - P1 Kapanış testi
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Dealer credentials
DEALER_EMAIL = "dealer1772201722@example.com"
DEALER_PASSWORD = "Dealer123!"

# Admin credentials (for edge case testing)
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def dealer_auth():
    """Authenticate as dealer and return token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD}
    )
    assert response.status_code == 200, f"Dealer login failed: {response.text}"
    data = response.json()
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"}
    }


@pytest.fixture(scope="module")
def admin_auth():
    """Authenticate as admin and return token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"}
    }


class TestDealerSettingsPreferences:
    """Tests for /api/dealer/settings/preferences endpoints"""

    def test_get_preferences_success(self, dealer_auth):
        """GET /api/dealer/settings/preferences - Should return notification prefs, blocked accounts, and security info"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers=dealer_auth["headers"]
        )
        assert response.status_code == 200, f"Get preferences failed: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "notification_prefs" in data
        assert "blocked_accounts" in data
        assert "security" in data
        
        # Validate notification_prefs structure
        prefs = data["notification_prefs"]
        assert "push_enabled" in prefs
        assert "email_enabled" in prefs
        assert "message_email_enabled" in prefs
        assert "marketing_email_enabled" in prefs
        assert "read_receipt_enabled" in prefs
        assert "sms_enabled" in prefs
        
        # Validate security structure
        security = data["security"]
        assert "two_factor_enabled" in security
        assert "last_login" in security

    def test_get_preferences_unauthorized(self):
        """GET /api/dealer/settings/preferences - Should fail without auth"""
        response = requests.get(f"{BASE_URL}/api/dealer/settings/preferences")
        assert response.status_code in [401, 403]

    def test_patch_preferences_toggle_enabled(self, dealer_auth):
        """PATCH /api/dealer/settings/preferences - Should update notification toggles"""
        # First get current state
        get_response = requests.get(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers=dealer_auth["headers"]
        )
        original_prefs = get_response.json()["notification_prefs"]
        
        # Toggle email_enabled
        new_email_value = not original_prefs["email_enabled"]
        
        response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers=dealer_auth["headers"],
            json={"notification_prefs": {"email_enabled": new_email_value}}
        )
        assert response.status_code == 200, f"Patch preferences failed: {response.text}"
        data = response.json()
        
        assert data["ok"] is True
        assert data["notification_prefs"]["email_enabled"] == new_email_value
        
        # Verify persistence with GET
        verify_response = requests.get(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers=dealer_auth["headers"]
        )
        assert verify_response.json()["notification_prefs"]["email_enabled"] == new_email_value

    def test_patch_preferences_multiple_fields(self, dealer_auth):
        """PATCH /api/dealer/settings/preferences - Should update multiple fields at once"""
        response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers=dealer_auth["headers"],
            json={
                "notification_prefs": {
                    "push_enabled": True,
                    "sms_enabled": True,
                    "marketing_email_enabled": False
                }
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["ok"] is True
        assert data["notification_prefs"]["push_enabled"] is True
        assert data["notification_prefs"]["sms_enabled"] is True
        assert data["notification_prefs"]["marketing_email_enabled"] is False


class TestDealerSettingsBlockedAccounts:
    """Tests for /api/dealer/settings/blocked-accounts endpoints"""

    def test_add_blocked_account_success(self, dealer_auth):
        """POST /api/dealer/settings/blocked-accounts - Should add email to blocked list"""
        test_email = f"test_blocked_{int(time.time())}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts",
            headers=dealer_auth["headers"],
            json={"email": test_email}
        )
        assert response.status_code == 200, f"Add blocked account failed: {response.text}"
        data = response.json()
        
        assert data["ok"] is True
        assert test_email.lower() in data["blocked_accounts"]
        
        # Cleanup - remove the blocked account
        requests.delete(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts?email={test_email}",
            headers=dealer_auth["headers"]
        )

    def test_add_blocked_account_duplicate(self, dealer_auth):
        """POST /api/dealer/settings/blocked-accounts - Adding duplicate should not error"""
        test_email = f"dup_blocked_{int(time.time())}@example.com"
        
        # Add first time
        response1 = requests.post(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts",
            headers=dealer_auth["headers"],
            json={"email": test_email}
        )
        assert response1.status_code == 200
        
        # Add second time (duplicate)
        response2 = requests.post(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts",
            headers=dealer_auth["headers"],
            json={"email": test_email}
        )
        assert response2.status_code == 200
        
        # Should still only appear once
        data = response2.json()
        count = data["blocked_accounts"].count(test_email.lower())
        assert count == 1, "Duplicate email should not be added twice"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts?email={test_email}",
            headers=dealer_auth["headers"]
        )

    def test_remove_blocked_account_success(self, dealer_auth):
        """DELETE /api/dealer/settings/blocked-accounts - Should remove email from blocked list"""
        test_email = f"remove_test_{int(time.time())}@example.com"
        
        # First add the email
        requests.post(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts",
            headers=dealer_auth["headers"],
            json={"email": test_email}
        )
        
        # Remove it
        response = requests.delete(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts?email={test_email}",
            headers=dealer_auth["headers"]
        )
        assert response.status_code == 200, f"Remove blocked account failed: {response.text}"
        data = response.json()
        
        assert data["ok"] is True
        assert test_email.lower() not in data["blocked_accounts"]

    def test_remove_nonexistent_blocked_account(self, dealer_auth):
        """DELETE /api/dealer/settings/blocked-accounts - Removing non-existent email should succeed"""
        nonexistent_email = f"never_existed_{int(time.time())}@example.com"
        
        response = requests.delete(
            f"{BASE_URL}/api/dealer/settings/blocked-accounts?email={nonexistent_email}",
            headers=dealer_auth["headers"]
        )
        # Should succeed silently
        assert response.status_code == 200


class TestDealerSettingsChangePassword:
    """Tests for /api/dealer/settings/change-password endpoint"""

    def test_change_password_wrong_current(self, dealer_auth):
        """POST /api/dealer/settings/change-password - Should fail with wrong current password"""
        response = requests.post(
            f"{BASE_URL}/api/dealer/settings/change-password",
            headers=dealer_auth["headers"],
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewValidPassword123!"
            }
        )
        assert response.status_code == 400, f"Should reject wrong current password: {response.text}"
        data = response.json()
        assert "Invalid current password" in data.get("detail", "")

    def test_change_password_too_short(self, dealer_auth):
        """POST /api/dealer/settings/change-password - Should fail with password less than 8 chars"""
        response = requests.post(
            f"{BASE_URL}/api/dealer/settings/change-password",
            headers=dealer_auth["headers"],
            json={
                "current_password": DEALER_PASSWORD,
                "new_password": "short"
            }
        )
        assert response.status_code == 400, f"Should reject short password: {response.text}"
        data = response.json()
        assert "too short" in data.get("detail", "").lower()

    def test_change_password_unauthorized(self):
        """POST /api/dealer/settings/change-password - Should fail without auth"""
        response = requests.post(
            f"{BASE_URL}/api/dealer/settings/change-password",
            json={
                "current_password": "any",
                "new_password": "NewPassword123!"
            }
        )
        assert response.status_code in [401, 403]


class TestDealerSettingsProfile:
    """Tests for /api/dealer/settings/profile endpoints"""

    def test_get_profile_success(self, dealer_auth):
        """GET /api/dealer/settings/profile - Should return dealer profile"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=dealer_auth["headers"]
        )
        assert response.status_code == 200, f"Get profile failed: {response.text}"
        data = response.json()
        
        assert "profile" in data
        profile = data["profile"]
        
        # Validate expected fields exist
        expected_fields = [
            "company_name", "authorized_person", "contact_email", "contact_phone",
            "address_street", "address_zip", "address_city", "address_country", "logo_url"
        ]
        for field in expected_fields:
            assert field in profile, f"Missing field: {field}"

    def test_patch_profile_success(self, dealer_auth):
        """PATCH /api/dealer/settings/profile - Should update profile fields"""
        unique_suffix = str(int(time.time()))[-4:]
        
        response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=dealer_auth["headers"],
            json={
                "company_name": f"Test Company {unique_suffix}",
                "address_city": "Test City"
            }
        )
        assert response.status_code == 200, f"Patch profile failed: {response.text}"
        data = response.json()
        assert data["ok"] is True
        
        # Verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=dealer_auth["headers"]
        )
        profile = get_response.json()["profile"]
        assert f"Test Company {unique_suffix}" in profile["company_name"]
        assert profile["address_city"] == "Test City"

    def test_patch_profile_empty_company_name(self, dealer_auth):
        """PATCH /api/dealer/settings/profile - Should fail with empty company_name"""
        response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=dealer_auth["headers"],
            json={"company_name": ""}
        )
        assert response.status_code == 400, f"Should reject empty company_name: {response.text}"


class TestDealerSettingsAuthorization:
    """Tests for authorization on dealer settings endpoints"""

    def test_admin_cannot_access_dealer_preferences(self, admin_auth):
        """Admin user should NOT access dealer settings endpoints"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers=admin_auth["headers"]
        )
        # Admin should be forbidden from dealer-only endpoints
        assert response.status_code in [401, 403], "Admin should not access dealer preferences"

    def test_admin_cannot_access_dealer_profile(self, admin_auth):
        """Admin user should NOT access dealer profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=admin_auth["headers"]
        )
        assert response.status_code in [401, 403], "Admin should not access dealer profile"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
