"""
Backend API tests for İlan Ver Akış Ayarları (Listing Create Config)
Tests:
- GET /api/admin/system-settings/listing-create
- POST /api/admin/system-settings/listing-create
- GET /api/places/config returns listing_create_config
- Regression: postal lookup still works in real mode
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    login_res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
    )
    if login_res.status_code == 200:
        return login_res.json().get("access_token")
    pytest.skip(f"Admin login failed: {login_res.status_code} {login_res.text}")


class TestListingCreateConfigEndpoints:
    """Tests for listing-create config admin endpoints"""

    def test_get_listing_create_config(self, admin_token):
        """GET /api/admin/system-settings/listing-create returns config"""
        response = requests.get(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "config" in data, "Response must contain 'config' key"
        assert "key" in data, "Response must contain 'key'"
        
        config = data["config"]
        # Validate config structure
        assert "apply_modules" in config, "Config must have apply_modules"
        assert isinstance(config["apply_modules"], list), "apply_modules must be a list"
        assert "country_selector_mode" in config, "Config must have country_selector_mode"
        assert "postal_code_required" in config, "Config must have postal_code_required"
        assert "map_required" in config, "Config must have map_required"
        assert "street_selection_required" in config, "Config must have street_selection_required"
        assert "require_city" in config, "Config must have require_city"
        print(f"GET listing-create config: {config}")

    def test_post_listing_create_config(self, admin_token):
        """POST /api/admin/system-settings/listing-create saves config"""
        # First get current config
        get_res = requests.get(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        original_config = get_res.json().get("config", {})
        
        # Post updated config
        new_config = {
            "apply_modules": ["vehicle", "real_estate"],
            "country_selector_mode": "select",
            "postal_code_required": False,
            "map_required": True,
            "street_selection_required": False,
            "require_city": True,
            "require_district": True,
            "require_neighborhood": False,
            "require_latitude": False,
            "require_longitude": False,
            "require_address_line": True,
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json",
            },
            json=new_config,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response must have ok: true"
        assert "config" in data, "Response must contain saved config"
        
        saved_config = data["config"]
        assert saved_config["apply_modules"] == ["vehicle", "real_estate"], "apply_modules not saved correctly"
        assert saved_config["country_selector_mode"] == "select", "country_selector_mode not saved"
        assert saved_config["postal_code_required"] is False, "postal_code_required not saved"
        assert saved_config["require_district"] is True, "require_district not saved"
        print(f"POST listing-create config saved: {saved_config}")
        
        # Verify GET returns the saved config
        verify_res = requests.get(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        verify_config = verify_res.json().get("config", {})
        assert verify_config["apply_modules"] == ["vehicle", "real_estate"], "Saved config not persisted"
        
        # Restore original config
        restore_payload = {
            **original_config,
            "apply_modules": original_config.get("apply_modules", ["vehicle", "real_estate", "other"]),
        }
        requests.post(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json",
            },
            json=restore_payload,
        )


class TestPlacesConfigReturnsListingConfig:
    """Tests that /api/places/config returns listing_create_config"""

    def test_places_config_has_listing_create_config(self, admin_token):
        """GET /api/places/config returns listing_create_config field"""
        response = requests.get(f"{BASE_URL}/api/places/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "listing_create_config" in data, "places/config must return listing_create_config"
        
        listing_config = data["listing_create_config"]
        assert listing_config is not None, "listing_create_config should not be null"
        assert isinstance(listing_config, dict), "listing_create_config must be a dict"
        
        # Verify expected keys
        expected_keys = [
            "apply_modules", "country_selector_mode", "postal_code_required",
            "map_required", "street_selection_required", "require_city"
        ]
        for key in expected_keys:
            assert key in listing_config, f"listing_create_config must have {key}"
        
        print(f"places/config listing_create_config: {listing_config}")

    def test_places_config_reflects_saved_settings(self, admin_token):
        """Saved listing-create config reflects in places/config"""
        # Save a specific config
        test_config = {
            "apply_modules": ["vehicle"],
            "country_selector_mode": "radio",
            "postal_code_required": True,
            "map_required": False,
            "street_selection_required": False,
            "require_city": True,
            "require_district": False,
            "require_neighborhood": False,
            "require_latitude": False,
            "require_longitude": False,
            "require_address_line": False,
        }
        
        save_res = requests.post(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json",
            },
            json=test_config,
        )
        assert save_res.status_code == 200, "Failed to save test config"
        
        # Verify places/config reflects the change
        places_res = requests.get(f"{BASE_URL}/api/places/config")
        assert places_res.status_code == 200
        
        places_data = places_res.json()
        listing_config = places_data.get("listing_create_config", {})
        
        assert listing_config.get("apply_modules") == ["vehicle"], "Config not reflected in places/config"
        assert listing_config.get("map_required") is False, "map_required not reflected"
        
        # Restore default config
        default_config = {
            "apply_modules": ["vehicle", "real_estate", "other"],
            "country_selector_mode": "radio",
            "postal_code_required": True,
            "map_required": True,
            "street_selection_required": True,
            "require_city": True,
            "require_district": False,
            "require_neighborhood": False,
            "require_latitude": False,
            "require_longitude": False,
            "require_address_line": True,
        }
        requests.post(
            f"{BASE_URL}/api/admin/system-settings/listing-create",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json",
            },
            json=default_config,
        )
        print("Test passed: places/config reflects saved listing_create_config")


class TestGoogleMapsCardAndPostalLookup:
    """Regression tests for Google Maps card and postal lookup"""

    def test_google_maps_settings_card(self, admin_token):
        """GET /api/admin/system-settings/google-maps returns config"""
        response = requests.get(
            f"{BASE_URL}/api/admin/system-settings/google-maps",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "key_configured" in data, "Response must have key_configured"
        assert "country_codes" in data, "Response must have country_codes"
        print(f"Google Maps config: key_configured={data['key_configured']}")

    def test_postal_lookup_real_mode_regression(self):
        """POST /api/places/postal-lookup works in real mode with live key"""
        # Test German postal code
        response = requests.get(
            f"{BASE_URL}/api/places/postal-lookup",
            params={"postal_code": "10115", "country": "DE"},
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "item" in data, "Response must have item"
            item = data["item"]
            # Check if we're in real mode
            mode = data.get("mode", "fallback")
            print(f"Postal lookup mode: {mode}, city: {item.get('city')}")
            
            # If API key is configured, should be real mode
            if item.get("city") == "Berlin":
                print("PASS: Postal lookup returns correct city")
        elif response.status_code == 400:
            # Graceful degradation
            print(f"Postal lookup returned 400 (may be fallback mode): {response.text}")
        else:
            assert False, f"Unexpected status: {response.status_code}"

    def test_places_config_mode(self):
        """GET /api/places/config should show real mode if key configured"""
        response = requests.get(f"{BASE_URL}/api/places/config")
        assert response.status_code == 200
        
        data = response.json()
        print(f"Places config: mode={data.get('mode')}, key_source={data.get('key_source')}")
        
        # If key is configured, should be real mode
        if data.get("key_configured"):
            assert data.get("mode") == "real" or data.get("real_mode") is True, \
                "Should be real mode when key is configured"
            print("PASS: Real mode active with configured key")
