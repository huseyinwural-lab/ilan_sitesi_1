"""
Test suite for iteration 106:
- Admin header management screen (guest/auth/corporate tabs)
- GET/PUT /api/admin/site/header endpoints
- GET /api/site/header public endpoint with mode parameter
- PUT /api/admin/site/header version increment check
- FAZ-3 academy feature flag in navigation-summary
- i18n/LanguageContext basic functionality
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Credentials
SUPER_ADMIN_EMAIL = "admin@platform.com"
SUPER_ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


class TestLogin:
    """Verify authentication works for testing."""

    def test_super_admin_login(self):
        """Test super_admin can log in."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user"]["role"] == "super_admin"
        print("PASS: super_admin login successful")

    def test_dealer_login(self):
        """Test dealer can log in."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        )
        assert response.status_code == 200, f"Dealer login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user"]["role"] == "dealer"
        print("PASS: dealer login successful")


class TestAdminSiteHeader:
    """Test /api/admin/site/header endpoints for super_admin."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token before each test."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        )
        assert response.status_code == 200
        self.admin_token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.admin_token}"}

    def test_admin_get_site_header(self):
        """GET /api/admin/site/header returns modes.guest/auth/corporate + logo_url."""
        response = requests.get(f"{BASE_URL}/api/admin/site/header", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "modes" in data, "Response must include 'modes' object"
        modes = data["modes"]
        
        assert "guest" in modes, "modes must have 'guest' key"
        assert "auth" in modes, "modes must have 'auth' key"
        assert "corporate" in modes, "modes must have 'corporate' key"
        
        # Each mode should have logo_url and items
        for mode_key in ["guest", "auth", "corporate"]:
            mode_data = modes[mode_key]
            assert "logo_url" in mode_data, f"{mode_key} must have logo_url"
            assert "items" in mode_data, f"{mode_key} must have items"
            assert isinstance(mode_data["items"], list), f"{mode_key}.items must be a list"
        
        # Check version and updated_at
        assert "version" in data or data.get("version") is not None, "version should exist"
        
        print(f"PASS: GET /api/admin/site/header returns correct structure with modes: {list(modes.keys())}")

    def test_admin_put_site_header_version_increment(self):
        """PUT /api/admin/site/header saves links and increments version."""
        # First get current version
        get_response = requests.get(f"{BASE_URL}/api/admin/site/header", headers=self.headers)
        assert get_response.status_code == 200
        current_data = get_response.json()
        current_version = current_data.get("version") or 0
        
        # Update with new link
        test_link = {
            "id": "test-link-iteration106",
            "label": "Test Link Iteration106",
            "url": "/test-page",
            "style": "text",
            "open_in_new_tab": False,
        }
        
        payload = {
            "modes": {
                "guest": {
                    "items": [test_link],
                },
                "auth": {
                    "items": current_data.get("modes", {}).get("auth", {}).get("items", []),
                },
                "corporate": {
                    "items": current_data.get("modes", {}).get("corporate", {}).get("items", []),
                },
            }
        }
        
        put_response = requests.put(
            f"{BASE_URL}/api/admin/site/header",
            headers=self.headers,
            json=payload,
        )
        assert put_response.status_code == 200, f"PUT failed: {put_response.text}"
        updated_data = put_response.json()
        
        # Verify version incremented
        new_version = updated_data.get("version") or 0
        assert new_version > current_version, f"Version should increment. Was {current_version}, now {new_version}"
        
        # Verify link was saved
        guest_items = updated_data.get("modes", {}).get("guest", {}).get("items", [])
        assert len(guest_items) > 0, "Guest items should not be empty after save"
        
        print(f"PASS: PUT /api/admin/site/header incremented version from {current_version} to {new_version}")

    def test_admin_header_not_accessible_without_token(self):
        """Verify /api/admin/site/header requires super_admin auth."""
        response = requests.get(f"{BASE_URL}/api/admin/site/header")
        assert response.status_code in [401, 403], f"Should be unauthorized without token, got {response.status_code}"
        print("PASS: Admin header endpoint protected correctly")


class TestPublicSiteHeader:
    """Test /api/site/header public endpoint."""

    def test_public_header_guest_mode(self):
        """GET /api/site/header?mode=guest returns correct config."""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=guest")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data.get("mode") == "guest", f"Expected mode=guest, got {data.get('mode')}"
        assert "logo_url" in data, "Response must include logo_url"
        assert "items" in data, "Response must include items"
        assert isinstance(data["items"], list), "items must be a list"
        
        print(f"PASS: GET /api/site/header?mode=guest returns correct structure, items count: {len(data['items'])}")

    def test_public_header_auth_mode(self):
        """GET /api/site/header?mode=auth returns correct config."""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=auth")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data.get("mode") == "auth", f"Expected mode=auth, got {data.get('mode')}"
        assert "logo_url" in data, "Response must include logo_url"
        assert "items" in data, "Response must include items"
        
        print(f"PASS: GET /api/site/header?mode=auth returns correct structure, items count: {len(data['items'])}")

    def test_public_header_corporate_mode(self):
        """GET /api/site/header?mode=corporate returns correct config."""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=corporate")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data.get("mode") == "corporate", f"Expected mode=corporate, got {data.get('mode')}"
        assert "logo_url" in data, "Response must include logo_url"
        assert "items" in data, "Response must include items"
        
        print(f"PASS: GET /api/site/header?mode=corporate returns correct structure, items count: {len(data['items'])}")

    def test_public_header_default_mode(self):
        """GET /api/site/header without mode defaults to guest."""
        response = requests.get(f"{BASE_URL}/api/site/header")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Default should be guest
        assert data.get("mode") == "guest", f"Default mode should be guest, got {data.get('mode')}"
        
        print("PASS: GET /api/site/header defaults to guest mode")


class TestDealerNavigationSummaryAcademy:
    """Test FAZ-3: academy.modules in /api/dealer/dashboard/navigation-summary."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Get dealer token before each test."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        )
        assert response.status_code == 200
        self.dealer_token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.dealer_token}"}

    def test_navigation_summary_academy_feature_flag(self):
        """
        FAZ-3: /api/dealer/dashboard/navigation-summary should return:
        - academy.modules: empty list (no MOCK content)
        - academy.data_source: feature_flag_disabled or feature_flag_enabled
        - academy.enabled: false (since seed has is_enabled=False)
        """
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/navigation-summary",
            headers=self.headers,
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify academy section exists
        assert "academy" in data, "Response must include 'academy' section"
        academy = data["academy"]
        
        # academy.modules must be empty (no MOCK content)
        assert "modules" in academy, "academy must have 'modules'"
        modules = academy["modules"]
        assert isinstance(modules, list), "academy.modules must be a list"
        assert len(modules) == 0, f"FAZ-3: academy.modules should be empty (no MOCK), got {modules}"
        
        # academy.data_source should indicate feature flag status
        assert "data_source" in academy, "academy must have 'data_source'"
        data_source = academy["data_source"]
        assert data_source in ["feature_flag_disabled", "feature_flag_enabled"], \
            f"data_source should be feature_flag_disabled/enabled, got {data_source}"
        
        # academy.enabled should match feature flag (seed has False)
        assert "enabled" in academy, "academy must have 'enabled'"
        # Since seed.py has academy.enabled = False, expect disabled
        if data_source == "feature_flag_disabled":
            assert academy["enabled"] is False, "academy.enabled should be False when flag disabled"
        
        print(f"PASS: FAZ-3 academy check - modules empty: {len(modules)==0}, data_source: {data_source}, enabled: {academy.get('enabled')}")

    def test_navigation_summary_badges(self):
        """Verify badges section exists with expected keys."""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/navigation-summary",
            headers=self.headers,
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "badges" in data, "Response must include 'badges'"
        badges = data["badges"]
        
        expected_keys = [
            "active_listings", "total_listings", "favorites_total",
            "unread_messages", "customers_total", "cart_total", "announcements_total"
        ]
        for key in expected_keys:
            assert key in badges, f"badges must have '{key}'"
            assert isinstance(badges[key], int), f"badges.{key} must be integer"
        
        print(f"PASS: Navigation summary badges present: {list(badges.keys())}")


class TestI18nLanguageContextIntegration:
    """Test i18n/LanguageContext integration - verify app loads correctly."""

    def test_homepage_loads(self):
        """Verify frontend homepage loads (basic health check)."""
        response = requests.get(BASE_URL, timeout=10)
        assert response.status_code == 200, f"Homepage failed to load: {response.status_code}"
        assert len(response.text) > 100, "Homepage content seems empty"
        print("PASS: Homepage loads correctly")

    def test_admin_login_page_loads(self):
        """Verify admin login page loads."""
        response = requests.get(f"{BASE_URL}/admin/login", timeout=10)
        assert response.status_code == 200, f"Admin login page failed: {response.status_code}"
        print("PASS: Admin login page loads")

    def test_public_header_endpoint_available(self):
        """Verify public header API is available for i18n context."""
        response = requests.get(f"{BASE_URL}/api/site/header?mode=guest")
        assert response.status_code == 200
        print("PASS: Public header endpoint available for i18n integration")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
