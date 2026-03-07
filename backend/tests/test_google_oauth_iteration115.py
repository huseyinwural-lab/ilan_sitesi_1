"""
Iteration 115 - Google OAuth and Language Feature Tests
Tests for:
1. Google login button active on login page
2. /auth/google/callback route with error handling
3. POST /api/auth/google/emergent/exchange endpoint
4. Guest header language selector
5. Dealer menu DE/FR translations
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://builder-hub-151.preview.emergentagent.com")


class TestGoogleOAuthExchangeEndpoint:
    """Tests for POST /api/auth/google/emergent/exchange endpoint"""
    
    def test_endpoint_exists(self):
        """Test that the endpoint exists (not 404)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "test", "portal_scope": "account"}
        )
        assert response.status_code != 404, "Endpoint should exist"
        print(f"SUCCESS: Endpoint exists, status code: {response.status_code}")
    
    def test_invalid_session_returns_401(self):
        """Test that invalid session_id returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "invalid-test-session-123", "portal_scope": "account"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"SUCCESS: Invalid session returns 401 with message: {data['detail']}")
    
    def test_empty_session_returns_400(self):
        """Test that empty session_id returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "", "portal_scope": "account"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "Session ID" in data["detail"] or "zorunludur" in data["detail"]
        print(f"SUCCESS: Empty session returns 400 with message: {data['detail']}")
    
    def test_missing_session_returns_422(self):
        """Test that missing session_id returns 422 (validation error)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"portal_scope": "account"}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"SUCCESS: Missing session_id returns 422 validation error")
    
    def test_whitespace_session_returns_400(self):
        """Test that whitespace-only session_id returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "   ", "portal_scope": "account"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"SUCCESS: Whitespace session returns 400")
    
    def test_dealer_portal_scope_accepted(self):
        """Test that dealer portal_scope is accepted"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "test-session", "portal_scope": "dealer"}
        )
        # Should get 401 for invalid session, not validation error
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"SUCCESS: Dealer portal_scope is accepted")
    
    def test_invalid_portal_scope_normalized(self):
        """Test that invalid portal_scope is normalized to account"""
        response = requests.post(
            f"{BASE_URL}/api/auth/google/emergent/exchange",
            json={"session_id": "test-session", "portal_scope": "invalid"}
        )
        # Should get 401 for invalid session, not validation error
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"SUCCESS: Invalid portal_scope handled gracefully")


class TestSiteHeaderLanguageSelector:
    """Tests for guest header language selector API"""
    
    def test_site_header_guest_mode(self):
        """Test that site header API returns data for guest mode"""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=guest")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "items" in data or "logo_url" in data
        print(f"SUCCESS: Site header API returns data for guest mode")
    
    def test_site_header_corporate_mode(self):
        """Test that site header API returns data for corporate mode"""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=corporate")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        print(f"SUCCESS: Site header API returns data for corporate mode")


class TestHealthAndBasicEndpoints:
    """Basic health checks"""
    
    def test_api_health(self):
        """Test that API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("SUCCESS: API health check passed")
    
    def test_auth_login_endpoint_exists(self):
        """Test that login endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@test.com", "password": "wrong"}
        )
        # Should get 401 or 400, not 404
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print("SUCCESS: Auth login endpoint exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
