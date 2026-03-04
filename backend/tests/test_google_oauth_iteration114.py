"""
Iteration 114 - Google OAuth / Login / Header Language / Dealer Menu Translation Tests
Features to test:
- Google login button active and clickable on login page
- Google callback route exists: /auth/google/callback
- Invalid session_id callback returns proper error message (no crash)
- Backend endpoint: POST /api/auth/google/emergent/exchange
- Backend invalid/empty session returns appropriate 4xx
- Guest header language selector visible
- Dealer menu labels show multi-level translation fallback (TR/DE/FR should not be empty)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE_URL = BASE_URL.rstrip('/')


class TestGoogleOAuthExchangeEndpoint:
    """Test POST /api/auth/google/emergent/exchange with various scenarios"""

    def test_exchange_endpoint_exists(self):
        """Verify endpoint exists (should not return 404)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "test", "portal_scope": "account"},
            headers={"Content-Type": "application/json"}
        )
        # 401 or 502 means endpoint exists but session invalid (expected behavior)
        # 404 would mean endpoint doesn't exist (failure)
        assert response.status_code != 404, f"Endpoint not found. Status: {response.status_code}"
        print(f"✓ Endpoint exists, returned status: {response.status_code}")

    def test_exchange_empty_session_id(self):
        """Empty session_id should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "", "portal_scope": "account"},
            headers={"Content-Type": "application/json"}
        )
        # Per code line 5293: "Session ID zorunludur" returns 400
        assert response.status_code == 400, f"Expected 400 for empty session_id, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Empty session_id returns 400 with detail: {data.get('detail')}")

    def test_exchange_missing_session_id(self):
        """Missing session_id field should return 422 (validation error)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"portal_scope": "account"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422, f"Expected 422 for missing session_id, got {response.status_code}"
        print(f"✓ Missing session_id returns 422 validation error")

    def test_exchange_invalid_session_id(self):
        """Invalid session_id should return 401 (Geçersiz veya süresi dolmuş Google oturumu)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "invalid-session-id-12345", "portal_scope": "account"},
            headers={"Content-Type": "application/json"}
        )
        # Per code line 5305: returns 401 for invalid session
        # Or 502 if Emergent server is unreachable
        assert response.status_code in [401, 502], f"Expected 401 or 502, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"✓ Invalid session_id returns {response.status_code} with detail: {data.get('detail')}")

    def test_exchange_whitespace_session_id(self):
        """Whitespace-only session_id should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "   ", "portal_scope": "account"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400 for whitespace session_id, got {response.status_code}"
        print(f"✓ Whitespace session_id returns 400")

    def test_exchange_dealer_portal_scope(self):
        """Dealer portal_scope should be accepted (still fails due to invalid session)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "test-invalid", "portal_scope": "dealer"},
            headers={"Content-Type": "application/json"}
        )
        # Should not return 400 for portal_scope value
        assert response.status_code != 400 or "portal" not in response.json().get("detail", "").lower()
        print(f"✓ Dealer portal_scope accepted, returned {response.status_code}")

    def test_exchange_invalid_portal_scope_normalized(self):
        """Invalid portal_scope should be normalized to 'account'"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "test", "portal_scope": "invalid_portal"},
            headers={"Content-Type": "application/json"}
        )
        # Should not reject the request due to portal_scope
        # Per code line 5354-5355: normalized to "account"
        assert response.status_code != 400 or "portal" not in response.json().get("detail", "").lower()
        print(f"✓ Invalid portal_scope normalized, returned {response.status_code}")


class TestDealerAuthEndpoints:
    """Test dealer login and auth functionality"""

    def test_dealer_login_endpoint(self):
        """Verify dealer can login with credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "dealer@platform.com",
                "password": "Dealer123!"
            },
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Dealer login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "dealer"
        print(f"✓ Dealer login successful, role: {data['user']['role']}")
        return data["access_token"]


class TestSiteHeaderAPI:
    """Test site header API for guest/auth modes"""

    def test_guest_header_mode(self):
        """GET /api/site/header?mode=guest returns items"""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=guest")
        assert response.status_code == 200, f"Guest header failed: {response.status_code}"
        data = response.json()
        print(f"✓ Guest header returned: logo_url={data.get('logo_url')}, items_count={len(data.get('items', []))}")
        return data

    def test_auth_header_mode(self):
        """GET /api/site/header?mode=auth returns items"""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=auth")
        assert response.status_code == 200, f"Auth header failed: {response.status_code}"
        data = response.json()
        print(f"✓ Auth header returned: logo_url={data.get('logo_url')}, items_count={len(data.get('items', []))}")
        return data

    def test_corporate_header_mode(self):
        """GET /api/site/header?mode=corporate returns items"""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=corporate")
        assert response.status_code == 200, f"Corporate header failed: {response.status_code}"
        data = response.json()
        print(f"✓ Corporate header returned: logo_url={data.get('logo_url')}, items_count={len(data.get('items', []))}")
        return data


class TestDealerNavigationSummary:
    """Test dealer dashboard navigation summary endpoint"""

    def test_navigation_summary_requires_auth(self):
        """GET /api/dealer/dashboard/navigation-summary without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Navigation summary requires auth, returned {response.status_code}")

    def test_navigation_summary_with_auth(self):
        """GET /api/dealer/dashboard/navigation-summary with dealer auth returns badges"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
            headers={"Content-Type": "application/json"}
        )
        if login_response.status_code != 200:
            pytest.skip("Dealer login failed, skipping authenticated test")

        token = login_response.json().get("access_token")
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/navigation-summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Navigation summary failed: {response.status_code}"
        data = response.json()
        assert "badges" in data
        print(f"✓ Navigation summary returned badges: {data.get('badges')}")
        return data


class TestDealerPortalConfig:
    """Test dealer portal config endpoint"""

    def test_dealer_portal_config_requires_auth(self):
        """GET /api/dealer/portal/config without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/dealer/portal/config")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Dealer portal config requires auth, returned {response.status_code}")

    def test_dealer_portal_config_with_auth(self):
        """GET /api/dealer/portal/config with dealer auth returns nav items"""
        # First login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
            headers={"Content-Type": "application/json"}
        )
        if login_response.status_code != 200:
            pytest.skip("Dealer login failed, skipping authenticated test")

        token = login_response.json().get("access_token")
        response = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Portal config failed: {response.status_code}"
        data = response.json()
        print(f"✓ Dealer portal config returned: {list(data.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
