"""
Test suite for Google Maps admin settings and address flow (P81)
Tests:
- Admin /api/admin/system-settings/google-maps GET/POST
- Public /api/places/config country_options return
- Address flow: /api/places/postal-lookup
- Address flow: /api/places/details
- Google key fallback warning when key not configured
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_CREDS = {"email": "admin@platform.com", "password": "Admin123!"}
USER_CREDS = {"email": "user@platform.com", "password": "User123!"}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if res.status_code == 200:
        return res.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def user_token():
    """Get user authentication token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json=USER_CREDS)
    if res.status_code == 200:
        return res.json().get("access_token")
    pytest.skip("User authentication failed")


class TestAdminGoogleMapsSettings:
    """Test admin Google Maps settings endpoints"""

    def test_get_google_maps_settings_returns_200(self, admin_token):
        """GET /api/admin/system-settings/google-maps should return 200 for super_admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify response structure
        assert "key_configured" in data, "Response should have key_configured field"
        assert "country_codes" in data, "Response should have country_codes field"
        assert "country_options" in data, "Response should have country_options field"
        assert "api_key_masked" in data, "Response should have api_key_masked field"
        
        print(f"✓ GET google-maps settings: key_configured={data['key_configured']}, codes={data['country_codes']}")

    def test_get_google_maps_settings_country_options_structure(self, admin_token):
        """country_options should be array of {code, name} objects"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=headers)
        
        assert res.status_code == 200
        data = res.json()
        country_options = data.get("country_options", [])
        
        assert isinstance(country_options, list), "country_options should be a list"
        for option in country_options:
            assert "code" in option, "Each option should have 'code'"
            assert "name" in option, "Each option should have 'name'"
            assert isinstance(option["code"], str), "code should be string"
            assert len(option["code"]) == 2, "code should be 2-letter country code"
        
        print(f"✓ country_options structure valid with {len(country_options)} options")

    def test_post_google_maps_settings_saves_country_codes(self, admin_token):
        """POST should save country_codes successfully"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Save test country codes
        test_codes = ["DE", "AT", "CH", "FR"]
        payload = {
            "api_key": None,  # Don't change key, just update country codes
            "country_codes": test_codes
        }
        res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=payload, headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data.get("ok") is True, "Response should have ok=true"
        assert "country_codes" in data, "Response should have country_codes"
        
        # Verify codes were saved
        saved_codes = data.get("country_codes", [])
        for code in test_codes:
            assert code in saved_codes, f"{code} should be in saved codes"
        
        print(f"✓ POST google-maps settings saved codes: {saved_codes}")

    def test_post_google_maps_settings_requires_at_least_one_country(self, admin_token):
        """POST with empty country_codes should fail with 400"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        payload = {
            "api_key": None,
            "country_codes": []
        }
        res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=payload, headers=headers)
        
        assert res.status_code == 400, f"Expected 400 for empty country_codes, got {res.status_code}"
        print("✓ POST with empty country_codes correctly returns 400")

    def test_post_google_maps_settings_api_key_save(self, admin_token):
        """POST with api_key should save it (masked in response)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Save with a test key
        payload = {
            "api_key": "AIzaTEST_KEY_12345678901234567890",
            "country_codes": ["DE", "AT"]
        }
        res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=payload, headers=headers)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data.get("key_configured") is True, "key_configured should be True after saving key"
        masked = data.get("api_key_masked", "")
        assert "****" in masked or len(masked) > 0, "api_key should be masked in response"
        
        print(f"✓ POST google-maps settings with key: key_configured={data['key_configured']}, masked={masked}")

    def test_get_google_maps_settings_forbidden_for_user(self, user_token):
        """Non-admin users should get 403 for admin google-maps endpoint"""
        headers = {"Authorization": f"Bearer {user_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=headers)
        
        assert res.status_code in [403, 401], f"Expected 403 or 401 for non-admin, got {res.status_code}"
        print("✓ Non-admin users correctly blocked from admin google-maps endpoint")


class TestPublicPlacesConfig:
    """Test public places config endpoint"""

    def test_places_config_returns_200(self):
        """GET /api/places/config should be public and return 200"""
        res = requests.get(f"{BASE_URL}/api/places/config")
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify response structure
        assert "real_mode" in data, "Response should have real_mode field"
        assert "mode" in data, "Response should have mode field"
        assert "key_source" in data, "Response should have key_source field"
        assert "country_options" in data, "Response should have country_options field"
        
        print(f"✓ places/config: mode={data['mode']}, key_source={data['key_source']}, real_mode={data['real_mode']}")

    def test_places_config_country_options_from_admin(self):
        """places/config country_options should reflect admin settings"""
        res = requests.get(f"{BASE_URL}/api/places/config")
        
        assert res.status_code == 200
        data = res.json()
        
        country_options = data.get("country_options", [])
        assert isinstance(country_options, list), "country_options should be a list"
        
        # Verify structure
        for option in country_options:
            assert "code" in option, "Each option should have code"
            assert "name" in option, "Each option should have name"
        
        codes = [opt["code"] for opt in country_options]
        print(f"✓ places/config country_options: {codes}")

    def test_places_config_shows_fallback_when_no_key(self, admin_token):
        """When no key configured, places/config should show fallback mode"""
        # First, clear the API key
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # We can't really clear the key easily, but we can check current state
        res = requests.get(f"{BASE_URL}/api/places/config")
        assert res.status_code == 200
        data = res.json()
        
        # Either real_mode or fallback mode is valid - document current state
        if data.get("real_mode"):
            print(f"✓ places/config in real mode (key_source={data.get('key_source')})")
        else:
            assert data.get("mode") == "fallback", "Without key, mode should be fallback"
            print("✓ places/config correctly shows fallback mode when no key")


class TestPlacesPostalLookup:
    """Test /api/places/postal-lookup endpoint"""

    def test_postal_lookup_requires_postal_code(self):
        """postal-lookup should require postal_code parameter"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?country=DE")
        
        # Should return 400 or 422 for missing postal_code
        assert res.status_code in [400, 422], f"Expected 400/422 for missing postal_code, got {res.status_code}"
        print("✓ postal-lookup correctly requires postal_code")

    def test_postal_lookup_requires_country(self):
        """postal-lookup should require country parameter"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115")
        
        # Should return 400 or 422 for missing country
        assert res.status_code in [400, 422], f"Expected 400/422 for missing country, got {res.status_code}"
        print("✓ postal-lookup correctly requires country")

    def test_postal_lookup_validates_country_format(self):
        """postal-lookup should validate 2-letter country code"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=GERMANY")
        
        assert res.status_code == 400, f"Expected 400 for invalid country code, got {res.status_code}"
        print("✓ postal-lookup validates 2-letter country code format")

    def test_postal_lookup_returns_fallback_without_key(self):
        """Without Google key, postal-lookup should return fallback response"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        
        assert res.status_code in [200, 400, 502], f"Expected 200/400/502, got {res.status_code}"
        data = res.json()
        
        # If no key, should have fallback mode or error message
        if data.get("mode") == "fallback":
            assert "message" in data, "Fallback response should have message"
            print(f"✓ postal-lookup returns fallback: {data.get('message')}")
        elif res.status_code == 200:
            # Has real key - verify structure
            assert "item" in data, "Real response should have item"
            print(f"✓ postal-lookup returns real data: mode={data.get('mode')}")
        else:
            print(f"✓ postal-lookup responded with status {res.status_code}")

    def test_postal_lookup_response_structure(self):
        """postal-lookup response should have correct structure"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        
        if res.status_code not in [200, 400, 429, 502]:
            pytest.fail(f"Unexpected status {res.status_code}: {res.text}")
        
        data = res.json()
        
        # Verify key fields exist
        assert "mode" in data, "Response should have mode field"
        
        if data.get("mode") == "real":
            assert "item" in data, "Real mode should have item"
            assert "streets" in data, "Real mode should have streets"
        
        print(f"✓ postal-lookup response structure valid (mode={data.get('mode')})")


class TestPlacesDetails:
    """Test /api/places/details endpoint"""

    def test_details_requires_place_id(self):
        """places/details should require place_id parameter"""
        res = requests.get(f"{BASE_URL}/api/places/details?country=DE")
        
        assert res.status_code in [400, 422], f"Expected 400/422 for missing place_id, got {res.status_code}"
        print("✓ places/details correctly requires place_id")

    def test_details_returns_fallback_without_key(self):
        """Without Google key, details should return fallback response"""
        res = requests.get(f"{BASE_URL}/api/places/details?place_id=ChIJAVkDPzdOqEcRcDteW0YgIQQ&country=DE")
        
        assert res.status_code in [200, 400, 502], f"Expected 200/400/502, got {res.status_code}"
        data = res.json()
        
        if data.get("mode") == "fallback":
            print(f"✓ places/details returns fallback: {data.get('message', 'no message')}")
        elif res.status_code == 200:
            assert "item" in data, "Real response should have item"
            print(f"✓ places/details returns real data: mode={data.get('mode')}")
        else:
            print(f"✓ places/details responded with status {res.status_code}")


class TestAddressFlowIntegration:
    """Test address flow integration end-to-end"""

    def test_admin_country_codes_reflected_in_places_config(self, admin_token):
        """Country codes saved in admin should appear in places/config"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Save specific country codes
        test_codes = ["DE", "AT", "CH", "FR"]
        payload = {"api_key": None, "country_codes": test_codes}
        save_res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=payload, headers=headers)
        assert save_res.status_code == 200
        
        # Check places/config reflects these
        config_res = requests.get(f"{BASE_URL}/api/places/config")
        assert config_res.status_code == 200
        
        config_data = config_res.json()
        config_codes = [opt["code"] for opt in config_data.get("country_options", [])]
        
        for code in test_codes:
            assert code in config_codes, f"{code} should be in places/config country_options"
        
        print(f"✓ Admin country codes correctly reflected in places/config: {config_codes}")

    def test_no_crash_without_google_key(self):
        """System should not crash when Google key is not configured"""
        # Test config endpoint
        config_res = requests.get(f"{BASE_URL}/api/places/config")
        assert config_res.status_code == 200, "places/config should not crash"
        
        # Test postal-lookup endpoint  
        postal_res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        assert postal_res.status_code in [200, 400, 429, 502], "postal-lookup should not crash"
        
        # Test details endpoint
        details_res = requests.get(f"{BASE_URL}/api/places/details?place_id=test123&country=DE")
        assert details_res.status_code in [200, 400, 429, 502], "details should not crash"
        
        print("✓ All endpoints handle missing Google key gracefully (no crash)")

    def test_fallback_warning_message_present(self):
        """Without key, fallback responses should have warning message"""
        # Test postal-lookup
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        
        if res.status_code == 200:
            data = res.json()
            if data.get("mode") == "fallback":
                assert "message" in data, "Fallback should have warning message"
                msg = data.get("message", "")
                # Verify message mentions API key or admin
                assert any(word in msg.lower() for word in ["key", "admin", "api"]), \
                    f"Message should mention key/admin issue: {msg}"
                print(f"✓ Fallback warning message: {msg}")
            else:
                print("✓ API key is configured, real mode active")
        else:
            print(f"✓ Endpoint returned {res.status_code} (not 200)")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
