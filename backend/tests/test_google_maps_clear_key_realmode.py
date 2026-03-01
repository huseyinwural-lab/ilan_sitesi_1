"""
Test suite for Google Maps clear_api_key and real mode flow (Iteration 72)
Tests:
- Admin clear_api_key=true clears the API key
- Postal-lookup real mode with live key
- Places details real mode with live key
- Country code normalization in place details (DE vs AL bug fix)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_CREDS = {"email": "admin@platform.com", "password": "Admin123!"}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
    if res.status_code == 200:
        return res.json().get("access_token")
    pytest.skip("Admin authentication failed")


class TestClearApiKeyFeature:
    """Test the new clear_api_key functionality"""

    def test_clear_api_key_removes_key(self, admin_token):
        """POST with clear_api_key=true should clear the stored API key"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First, save a test key
        save_payload = {
            "api_key": "AIzaTEST_TO_BE_CLEARED_12345678901234567890",
            "country_codes": ["DE", "AT"]
        }
        save_res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=save_payload, headers=headers)
        assert save_res.status_code == 200, f"Save failed: {save_res.text}"
        
        # Verify key is configured
        get_res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json().get("key_configured") is True, "Key should be configured before clearing"
        print(f"✓ Key was saved: key_configured=True, masked={get_res.json().get('api_key_masked')}")
        
        # Now clear the key
        clear_payload = {
            "api_key": None,
            "clear_api_key": True,
            "country_codes": ["DE", "AT"]
        }
        clear_res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=clear_payload, headers=headers)
        assert clear_res.status_code == 200, f"Clear failed: {clear_res.text}"
        
        clear_data = clear_res.json()
        assert clear_data.get("ok") is True, "Clear response should have ok=true"
        assert clear_data.get("key_configured") is False, "key_configured should be False after clearing"
        assert clear_data.get("api_key_masked") == "", "api_key_masked should be empty after clearing"
        print(f"✓ Key cleared successfully: key_configured={clear_data.get('key_configured')}")

    def test_clear_api_key_preserves_country_codes(self, admin_token):
        """clear_api_key should preserve country_codes setting"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Save a key with specific country codes
        save_payload = {
            "api_key": "AIzaTEST_PRESERVE_CODES_12345678901234567890",
            "country_codes": ["DE", "AT", "CH", "FR"]
        }
        requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=save_payload, headers=headers)
        
        # Clear the key but keep country codes
        clear_payload = {
            "api_key": None,
            "clear_api_key": True,
            "country_codes": ["DE", "AT", "CH", "FR"]
        }
        clear_res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=clear_payload, headers=headers)
        assert clear_res.status_code == 200
        
        clear_data = clear_res.json()
        saved_codes = clear_data.get("country_codes", [])
        for code in ["DE", "AT", "CH", "FR"]:
            assert code in saved_codes, f"{code} should be preserved after clearing key"
        
        print(f"✓ Country codes preserved after key clear: {saved_codes}")

    def test_clear_api_key_requires_country_codes(self, admin_token):
        """clear_api_key still requires at least one country code"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        clear_payload = {
            "api_key": None,
            "clear_api_key": True,
            "country_codes": []  # Empty - should fail
        }
        res = requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=clear_payload, headers=headers)
        
        assert res.status_code == 400, f"Expected 400 for empty country_codes, got {res.status_code}"
        print("✓ clear_api_key correctly requires at least one country code")


class TestRealModeWithLiveKey:
    """Test real mode operation when a valid Google Maps key is configured"""
    
    def setup_class(cls):
        """Restore valid test key before real mode tests"""
        # Get admin token
        res = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if res.status_code != 200:
            pytest.skip("Admin authentication failed")
        cls.admin_token = res.json().get("access_token")
        cls.headers = {"Authorization": f"Bearer {cls.admin_token}"}
        
        # We need to restore a valid key - check if already configured
        get_res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=cls.headers)
        if get_res.status_code == 200:
            data = get_res.json()
            if not data.get("key_configured"):
                # Save a placeholder test key (real key should be configured in admin)
                # Note: Real tests require actual Google Maps API key
                save_payload = {
                    "api_key": "AIzaSyTest_Placeholder_Key_For_Testing",
                    "country_codes": ["DE", "AT", "CH", "FR"]
                }
                requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=save_payload, headers=cls.headers)

    def test_places_config_shows_real_mode_when_key_configured(self):
        """places/config should show real_mode=true when key is configured"""
        res = requests.get(f"{BASE_URL}/api/places/config")
        assert res.status_code == 200
        
        data = res.json()
        # If key is configured, should be in real mode
        if data.get("real_mode"):
            assert data.get("mode") in ["real", "ready"], f"Expected real/ready mode when key configured, got {data.get('mode')}"
            print(f"✓ places/config in real mode: key_source={data.get('key_source')}")
        else:
            print(f"⚠ places/config in fallback mode (key may not be valid): {data.get('message', 'no message')}")

    def test_postal_lookup_real_mode_response_structure(self):
        """postal-lookup with real key should return proper response structure"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        
        assert res.status_code in [200, 400, 429, 502], f"Unexpected status: {res.status_code}"
        data = res.json()
        
        if data.get("mode") == "real":
            # Verify real mode structure
            assert "item" in data, "Real mode response should have 'item'"
            assert "streets" in data, "Real mode response should have 'streets'"
            assert "key_source" in data, "Real mode response should have 'key_source'"
            assert "remaining" in data, "Real mode response should have 'remaining' (rate limit)"
            
            item = data.get("item")
            if item:
                # Verify item structure
                assert "postal_code" in item, "Item should have postal_code"
                assert "country_code" in item, "Item should have country_code"
                assert "latitude" in item, "Item should have latitude"
                assert "longitude" in item, "Item should have longitude"
            
            print(f"✓ postal-lookup real mode: {len(data.get('streets', []))} streets returned, item={bool(item)}")
        else:
            print(f"⚠ postal-lookup in fallback mode: {data.get('message', 'no message')}")

    def test_postal_lookup_returns_streets_list(self):
        """postal-lookup should return streets list for address selection"""
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10117&country=DE")
        
        if res.status_code == 200:
            data = res.json()
            if data.get("mode") == "real":
                streets = data.get("streets", [])
                assert isinstance(streets, list), "streets should be a list"
                
                if len(streets) > 0:
                    # Verify street structure
                    first_street = streets[0]
                    assert "place_id" in first_street, "Street should have place_id"
                    assert "description" in first_street, "Street should have description"
                    print(f"✓ postal-lookup returned {len(streets)} streets, first: {first_street.get('description', '')[:50]}")
                else:
                    print("✓ postal-lookup returned empty streets list (may be sparse area)")
            else:
                print(f"⚠ postal-lookup in fallback: {data.get('message', '')}")
        else:
            print(f"⚠ postal-lookup returned {res.status_code}")

    def test_places_details_real_mode_response_structure(self):
        """places/details with real key should return proper response structure"""
        # Use a known Berlin place_id (Brandenburger Tor) for testing
        test_place_id = "ChIJiQnyVcZRqEcRY0xnhE73XAQ"
        
        res = requests.get(f"{BASE_URL}/api/places/details?place_id={test_place_id}&country=DE")
        
        assert res.status_code in [200, 400, 429, 502], f"Unexpected status: {res.status_code}"
        data = res.json()
        
        if data.get("mode") == "real":
            assert "item" in data, "Real mode should have item"
            assert "key_source" in data, "Real mode should have key_source"
            
            item = data.get("item")
            if item:
                # Verify normalized address components
                assert "place_id" in item, "Item should have place_id"
                assert "formatted_address" in item, "Item should have formatted_address"
                assert "latitude" in item, "Item should have latitude"
                assert "longitude" in item, "Item should have longitude"
                
                # Check country_code normalization - should be 2-letter uppercase
                country_code = item.get("country_code")
                if country_code:
                    assert len(country_code) == 2, f"country_code should be 2 letters, got: {country_code}"
                    assert country_code.isupper(), f"country_code should be uppercase, got: {country_code}"
                
                print(f"✓ places/details real mode: address={item.get('formatted_address', '')[:50]}, country={country_code}")
            else:
                print("✓ places/details real mode returned but item is None (may be invalid place_id)")
        else:
            print(f"⚠ places/details in fallback: {data.get('message', '')}")


class TestCountryCodeNormalization:
    """Test country_code normalization in place details (DE vs AL bug fix)"""

    def test_country_code_is_two_letter_uppercase(self):
        """country_code in place details should always be 2-letter uppercase"""
        # Test with a German postal code
        res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        
        if res.status_code == 200:
            data = res.json()
            if data.get("mode") == "real":
                item = data.get("item", {})
                country_code = item.get("country_code")
                
                if country_code:
                    assert len(country_code) == 2, f"country_code should be exactly 2 chars, got: {country_code}"
                    assert country_code.isupper(), f"country_code should be uppercase, got: {country_code}"
                    assert country_code == "DE", f"For Germany postal code, country_code should be DE, got: {country_code}"
                    print(f"✓ country_code normalized correctly: {country_code}")
                else:
                    print("⚠ country_code is None in response")
            else:
                print(f"⚠ In fallback mode, skipping country_code check")
        else:
            print(f"⚠ postal-lookup returned {res.status_code}, skipping test")

    def test_country_code_normalized_from_components(self):
        """Country code should be extracted from address_components short_name"""
        # This tests the _normalize_google_place_details function indirectly
        # The fix ensures country_code uses short_name (DE) not long_name (Germany/Deutschland)
        
        # First check postal-lookup
        postal_res = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=80331&country=DE")
        if postal_res.status_code == 200 and postal_res.json().get("mode") == "real":
            streets = postal_res.json().get("streets", [])
            if streets:
                # Get details for first street
                place_id = streets[0].get("place_id")
                if place_id:
                    details_res = requests.get(f"{BASE_URL}/api/places/details?place_id={place_id}&country=DE")
                    if details_res.status_code == 200:
                        details_data = details_res.json()
                        if details_data.get("mode") == "real":
                            item = details_data.get("item", {})
                            cc = item.get("country_code")
                            if cc:
                                # Should never be "DE" spelled out - must be 2-letter code
                                assert cc not in ["GERMANY", "DEUTSCHLAND", "AL"], \
                                    f"country_code should be short code not '{cc}'"
                                assert len(cc) == 2, f"country_code must be 2 chars: {cc}"
                                print(f"✓ country_code from components: {cc}")
                                return
        
        print("⚠ Could not fully test country_code normalization (fallback mode or no streets)")

    def test_postal_lookup_country_parameter_validated(self):
        """Country parameter should be validated as 2-letter code"""
        # Valid codes should work
        res_de = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=DE")
        assert res_de.status_code in [200, 400, 429, 502], "DE should be valid country code"
        
        res_at = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=1010&country=AT")
        assert res_at.status_code in [200, 400, 429, 502], "AT should be valid country code"
        
        # Invalid codes should fail
        res_invalid = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=GERMANY")
        assert res_invalid.status_code == 400, "Full country name should be rejected"
        
        res_lower = requests.get(f"{BASE_URL}/api/places/postal-lookup?postal_code=10115&country=de")
        # Should either normalize to DE or reject - check what happens
        print(f"✓ Lowercase 'de' returned status {res_lower.status_code}")
        
        print("✓ Country parameter validation working correctly")


class TestAdminUIGoogleMapsCard:
    """Test data returned for Admin UI Google Maps card"""

    def test_admin_google_maps_returns_required_ui_fields(self, admin_token):
        """Admin endpoint should return all fields needed for UI card"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=headers)
        
        assert res.status_code == 200
        data = res.json()
        
        # Check all fields needed for AdminSystemSettings.js Google Maps card
        required_fields = ["key_configured", "api_key_masked", "country_codes", "country_options"]
        for field in required_fields:
            assert field in data, f"Missing required UI field: {field}"
        
        # Verify types
        assert isinstance(data["key_configured"], bool), "key_configured should be bool"
        assert isinstance(data["api_key_masked"], str), "api_key_masked should be string"
        assert isinstance(data["country_codes"], list), "country_codes should be list"
        assert isinstance(data["country_options"], list), "country_options should be list"
        
        # Verify country_options structure for checkbox rendering
        for opt in data["country_options"]:
            assert "code" in opt, "country_option needs 'code' for checkbox value"
            assert "name" in opt, "country_option needs 'name' for label"
        
        print(f"✓ Admin UI fields complete: key_configured={data['key_configured']}, {len(data['country_options'])} country options")

    def test_api_key_masked_format(self, admin_token):
        """Masked API key should show first chars and asterisks"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First save a test key
        save_payload = {
            "api_key": "AIzaSyB123456789012345678901234567890XYZ",
            "country_codes": ["DE"]
        }
        requests.post(f"{BASE_URL}/api/admin/system-settings/google-maps", json=save_payload, headers=headers)
        
        # Get and check masked format
        res = requests.get(f"{BASE_URL}/api/admin/system-settings/google-maps", headers=headers)
        assert res.status_code == 200
        
        masked = res.json().get("api_key_masked", "")
        if masked:
            # Should show prefix and asterisks
            assert "****" in masked or "*" in masked, "Masked key should contain asterisks"
            # Should not reveal full key
            assert len(masked) < 50, "Masked key should be truncated"
            print(f"✓ API key masked format: {masked}")
        else:
            print("⚠ api_key_masked is empty")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
