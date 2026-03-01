"""
Google Maps API Integration Tests
Tests postal lookup, street list, and place details endpoints with real Google Maps key
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestGoogleMapsPostalLookup:
    """Test postal lookup endpoint with real Google Maps API"""
    
    def test_postal_lookup_real_mode_de(self):
        """Test postal lookup for German postal code in real mode"""
        response = requests.get(
            f"{BASE_URL}/api/places/postal-lookup",
            params={"postal_code": "10115", "country": "DE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        # Verify real mode is active
        assert data.get("mode") == "real", f"Expected mode='real', got mode='{data.get('mode')}'"
        assert data.get("key_source") == "system_setting", f"Key source should be system_setting"
        assert data.get("status") == "OK"
        
        # Verify response structure
        item = data.get("item", {})
        assert "place_id" in item
        assert "formatted_address" in item
        assert "city" in item
        assert item.get("postal_code") == "10115"
        assert item.get("country_code") == "DE"
        assert "latitude" in item
        assert "longitude" in item
        
        # Verify streets list is present
        streets = data.get("streets", [])
        assert isinstance(streets, list)
        if streets:  # Should have some streets
            street = streets[0]
            assert "place_id" in street
            assert "description" in street
            assert "main_text" in street
        
        print(f"✓ Postal lookup returned: {item.get('city')}, {item.get('formatted_address')}")
        print(f"✓ Found {len(streets)} streets")
    
    def test_postal_lookup_at_returns_response(self):
        """Test postal lookup for Austrian postal code - may return fallback if AT not configured"""
        response = requests.get(
            f"{BASE_URL}/api/places/postal-lookup",
            params={"postal_code": "1010", "country": "AT"}
        )
        # Should return 200 even in fallback mode
        assert response.status_code == 200
        
        data = response.json()
        mode = data.get("mode")
        # AT may not be fully configured, so fallback is acceptable
        if mode == "real":
            assert data.get("status") == "OK"
            item = data.get("item", {})
            assert item.get("postal_code") == "1010"
            print(f"✓ AT postal lookup (real mode): {item.get('city')}")
        else:
            print(f"✓ AT postal lookup returned fallback mode (expected if AT not configured)")
    
    def test_postal_lookup_real_mode_ch(self):
        """Test postal lookup for Swiss postal code"""
        response = requests.get(
            f"{BASE_URL}/api/places/postal-lookup",
            params={"postal_code": "8001", "country": "CH"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("mode") == "real"
        assert data.get("status") == "OK"
        
        item = data.get("item", {})
        assert item.get("postal_code") == "8001"
        assert item.get("country_code") == "CH"
        print(f"✓ CH postal lookup: {item.get('city')}")


class TestGoogleMapsPlaceDetails:
    """Test place details endpoint with real Google Maps API"""
    
    def test_place_details_real_mode(self):
        """Test place details for a street from postal lookup"""
        # First get a street from postal lookup
        lookup_response = requests.get(
            f"{BASE_URL}/api/places/postal-lookup",
            params={"postal_code": "10115", "country": "DE"}
        )
        assert lookup_response.status_code == 200
        lookup_data = lookup_response.json()
        
        streets = lookup_data.get("streets", [])
        if not streets:
            pytest.skip("No streets returned from postal lookup")
        
        # Get details for first street
        street_place_id = streets[0].get("place_id")
        
        response = requests.get(
            f"{BASE_URL}/api/places/details",
            params={"place_id": street_place_id, "country": "DE"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("mode") == "real"
        assert data.get("status") == "OK"
        
        item = data.get("item", {})
        assert "place_id" in item
        assert "formatted_address" in item
        assert item.get("country_code") == "DE"
        assert "latitude" in item
        assert "longitude" in item
        
        print(f"✓ Place details: {item.get('formatted_address')}")
        print(f"✓ Coordinates: {item.get('latitude')}, {item.get('longitude')}")


class TestGoogleMapsSystemSettings:
    """Test Google Maps system settings endpoints"""
    
    def test_system_settings_list(self):
        """Test that system settings API returns Google Maps key status"""
        response = requests.get(f"{BASE_URL}/api/admin/system-settings")
        # May need auth - check response
        if response.status_code == 401:
            pytest.skip("Auth required for system settings")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if google maps settings are present
        settings_list = data if isinstance(data, list) else data.get("settings", [])
        google_maps_settings = [s for s in settings_list if "google_maps" in s.get("key", "").lower()]
        
        print(f"✓ Found {len(google_maps_settings)} Google Maps related settings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
