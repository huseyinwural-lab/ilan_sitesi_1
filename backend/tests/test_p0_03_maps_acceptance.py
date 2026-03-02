"""
P0-03 Maps Live Acceptance Tests
================================
Validates Google Maps/Places integration for 3 cities:
- TR Istanbul (34000)
- DE Berlin (10115) 
- FR Paris (75001)

Tests verify:
1. GET /api/places/config - real_mode=true, key_source=system_setting
2. GET /api/places/postal-lookup - status=OK for each city
3. DB assertions - listing location fields populated
4. Acceptance report consistency
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test context from p0_03_maps_context.json
TEST_CONTEXT = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1MGI3NzA4YS00MzU4LTQwNTEtYWZlNy0yNTczNjZmZDg5MzQiLCJlbWFpbCI6InVzZXJAcGxhdGZvcm0uY29tIiwicm9sZSI6ImluZGl2aWR1YWwiLCJwb3J0YWxfc2NvcGUiOiJhY2NvdW50IiwidG9rZW5fdmVyc2lvbiI6InYyIiwiZXhwIjoxNzcyNDg1ODE3LCJ0eXBlIjoiYWNjZXNzIn0.raOCyzvHOXzbwLW24ldgPRtx6Uw1t5xzw170dwnWmvI",
    "cases": [
        {
            "label": "TR-Istanbul",
            "country": "TR",
            "postal_code": "34000",
            "listing_id": "f7b2c030-ac08-40af-8530-fca446a244f1",
            "expected_city": "İstanbul",
            "expected_district": "Maltepe"
        },
        {
            "label": "DE-Berlin",
            "country": "DE",
            "postal_code": "10115",
            "listing_id": "8edea369-d74f-4638-aeec-0fe314fafb79",
            "expected_city": "Berlin",
            "expected_district": "Mitte"
        },
        {
            "label": "FR-Paris",
            "country": "FR",
            "postal_code": "75001",
            "listing_id": "b356e36b-5912-467a-996f-5017f63784a2",
            "expected_city": "Île-de-France",
            "expected_district": "Paris"
        }
    ]
}


@pytest.fixture
def api_client():
    """Requests session with default headers"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_headers():
    """Authorization headers with access token"""
    return {"Authorization": f"Bearer {TEST_CONTEXT['access_token']}"}


class TestPlacesConfig:
    """Verify /api/places/config returns real_mode=true with correct key_source"""

    def test_places_config_status_200(self, api_client):
        """GET /api/places/config returns 200"""
        response = api_client.get(f"{BASE_URL}/api/places/config")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: /api/places/config returns 200")

    def test_places_config_real_mode_true(self, api_client):
        """real_mode should be true (Google API key configured)"""
        response = api_client.get(f"{BASE_URL}/api/places/config")
        data = response.json()
        assert data.get("real_mode") is True, f"Expected real_mode=True, got {data.get('real_mode')}"
        print(f"PASS: real_mode={data.get('real_mode')}")

    def test_places_config_key_source_system_setting(self, api_client):
        """key_source should be 'system_setting' (admin configured)"""
        response = api_client.get(f"{BASE_URL}/api/places/config")
        data = response.json()
        assert data.get("key_source") == "system_setting", f"Expected key_source=system_setting, got {data.get('key_source')}"
        print(f"PASS: key_source={data.get('key_source')}")

    def test_places_config_mode_real(self, api_client):
        """mode should be 'real'"""
        response = api_client.get(f"{BASE_URL}/api/places/config")
        data = response.json()
        assert data.get("mode") == "real", f"Expected mode=real, got {data.get('mode')}"
        print(f"PASS: mode={data.get('mode')}")

    def test_places_config_country_options_includes_test_countries(self, api_client):
        """country_options should include TR, DE, FR"""
        response = api_client.get(f"{BASE_URL}/api/places/config")
        data = response.json()
        country_codes = [c.get("code") for c in data.get("country_options", [])]
        for expected_code in ["TR", "DE", "FR"]:
            assert expected_code in country_codes, f"Expected {expected_code} in country_options, got {country_codes}"
        print(f"PASS: country_options includes TR, DE, FR: {country_codes}")


class TestPostalLookupTRIstanbul:
    """Verify postal lookup for TR-Istanbul (34000)"""

    def test_postal_lookup_tr_status_200(self, api_client):
        """GET /api/places/postal-lookup?postal_code=34000&country=TR returns 200"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "34000", "country": "TR"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: TR-Istanbul postal lookup returns 200")

    def test_postal_lookup_tr_status_ok(self, api_client):
        """status should be 'OK'"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "34000", "country": "TR"})
        data = response.json()
        assert data.get("status") == "OK", f"Expected status=OK, got {data.get('status')}"
        print(f"PASS: TR-Istanbul status={data.get('status')}")

    def test_postal_lookup_tr_has_item(self, api_client):
        """Response should have item with location data"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "34000", "country": "TR"})
        data = response.json()
        item = data.get("item")
        assert item is not None, "Expected item in response"
        assert item.get("city") == "İstanbul", f"Expected city=İstanbul, got {item.get('city')}"
        assert item.get("district") == "Maltepe", f"Expected district=Maltepe, got {item.get('district')}"
        assert item.get("latitude") is not None, "Expected latitude in item"
        assert item.get("longitude") is not None, "Expected longitude in item"
        print(f"PASS: TR-Istanbul item has city={item.get('city')}, district={item.get('district')}, lat={item.get('latitude')}, lng={item.get('longitude')}")

    def test_postal_lookup_tr_has_streets(self, api_client):
        """Response should have streets array"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "34000", "country": "TR"})
        data = response.json()
        streets = data.get("streets", [])
        assert len(streets) > 0, "Expected at least 1 street in response"
        print(f"PASS: TR-Istanbul has {len(streets)} street suggestions")


class TestPostalLookupDEBerlin:
    """Verify postal lookup for DE-Berlin (10115)"""

    def test_postal_lookup_de_status_200(self, api_client):
        """GET /api/places/postal-lookup?postal_code=10115&country=DE returns 200"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "10115", "country": "DE"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: DE-Berlin postal lookup returns 200")

    def test_postal_lookup_de_status_ok(self, api_client):
        """status should be 'OK'"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "10115", "country": "DE"})
        data = response.json()
        assert data.get("status") == "OK", f"Expected status=OK, got {data.get('status')}"
        print(f"PASS: DE-Berlin status={data.get('status')}")

    def test_postal_lookup_de_has_item(self, api_client):
        """Response should have item with location data"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "10115", "country": "DE"})
        data = response.json()
        item = data.get("item")
        assert item is not None, "Expected item in response"
        assert item.get("city") == "Berlin", f"Expected city=Berlin, got {item.get('city')}"
        assert item.get("district") == "Mitte", f"Expected district=Mitte, got {item.get('district')}"
        assert item.get("latitude") is not None, "Expected latitude in item"
        assert item.get("longitude") is not None, "Expected longitude in item"
        print(f"PASS: DE-Berlin item has city={item.get('city')}, district={item.get('district')}, lat={item.get('latitude')}, lng={item.get('longitude')}")

    def test_postal_lookup_de_has_streets(self, api_client):
        """Response should have streets array"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "10115", "country": "DE"})
        data = response.json()
        streets = data.get("streets", [])
        assert len(streets) > 0, "Expected at least 1 street in response"
        print(f"PASS: DE-Berlin has {len(streets)} street suggestions")


class TestPostalLookupFRParis:
    """Verify postal lookup for FR-Paris (75001)"""

    def test_postal_lookup_fr_status_200(self, api_client):
        """GET /api/places/postal-lookup?postal_code=75001&country=FR returns 200"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "75001", "country": "FR"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: FR-Paris postal lookup returns 200")

    def test_postal_lookup_fr_status_ok(self, api_client):
        """status should be 'OK'"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "75001", "country": "FR"})
        data = response.json()
        assert data.get("status") == "OK", f"Expected status=OK, got {data.get('status')}"
        print(f"PASS: FR-Paris status={data.get('status')}")

    def test_postal_lookup_fr_has_item(self, api_client):
        """Response should have item with location data"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "75001", "country": "FR"})
        data = response.json()
        item = data.get("item")
        assert item is not None, "Expected item in response"
        assert item.get("city") == "Île-de-France", f"Expected city=Île-de-France, got {item.get('city')}"
        assert item.get("district") == "Paris", f"Expected district=Paris, got {item.get('district')}"
        assert item.get("latitude") is not None, "Expected latitude in item"
        assert item.get("longitude") is not None, "Expected longitude in item"
        print(f"PASS: FR-Paris item has city={item.get('city')}, district={item.get('district')}, lat={item.get('latitude')}, lng={item.get('longitude')}")

    def test_postal_lookup_fr_has_streets(self, api_client):
        """Response should have streets array"""
        response = api_client.get(f"{BASE_URL}/api/places/postal-lookup", params={"postal_code": "75001", "country": "FR"})
        data = response.json()
        streets = data.get("streets", [])
        assert len(streets) > 0, "Expected at least 1 street in response"
        print(f"PASS: FR-Paris has {len(streets)} street suggestions")


class TestDBAssertionsTRIstanbul:
    """Verify DB persistence for TR-Istanbul listing"""

    def test_listing_tr_exists(self, api_client, auth_headers):
        """Listing f7b2c030-ac08-40af-8530-fca446a244f1 should exist"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: TR-Istanbul listing {listing_id} exists")

    def test_listing_tr_location_country(self, api_client, auth_headers):
        """location.country should be TR"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("country") == "TR", f"Expected country=TR, got {location.get('country')}"
        print(f"PASS: TR-Istanbul location.country={location.get('country')}")

    def test_listing_tr_location_city(self, api_client, auth_headers):
        """location.city should be İstanbul"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("city") == "İstanbul", f"Expected city=İstanbul, got {location.get('city')}"
        print(f"PASS: TR-Istanbul location.city={location.get('city')}")

    def test_listing_tr_location_district(self, api_client, auth_headers):
        """location.district should be Maltepe"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("district") == "Maltepe", f"Expected district=Maltepe, got {location.get('district')}"
        print(f"PASS: TR-Istanbul location.district={location.get('district')}")

    def test_listing_tr_location_postal_code(self, api_client, auth_headers):
        """location.postal_code should be 34000"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("postal_code") == "34000", f"Expected postal_code=34000, got {location.get('postal_code')}"
        print(f"PASS: TR-Istanbul location.postal_code={location.get('postal_code')}")

    def test_listing_tr_location_lat_lng(self, api_client, auth_headers):
        """location.latitude and longitude should be set"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("latitude") is not None, "Expected latitude to be set"
        assert location.get("longitude") is not None, "Expected longitude to be set"
        print(f"PASS: TR-Istanbul lat={location.get('latitude')}, lng={location.get('longitude')}")

    def test_listing_tr_location_address_line(self, api_client, auth_headers):
        """location.address_line should be set"""
        listing_id = "f7b2c030-ac08-40af-8530-fca446a244f1"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("address_line") is not None and len(location.get("address_line", "")) > 0, "Expected address_line to be set"
        print(f"PASS: TR-Istanbul location.address_line={location.get('address_line')}")


class TestDBAssertionsDEBerlin:
    """Verify DB persistence for DE-Berlin listing"""

    def test_listing_de_exists(self, api_client, auth_headers):
        """Listing 8edea369-d74f-4638-aeec-0fe314fafb79 should exist"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: DE-Berlin listing {listing_id} exists")

    def test_listing_de_location_country(self, api_client, auth_headers):
        """location.country should be DE"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("country") == "DE", f"Expected country=DE, got {location.get('country')}"
        print(f"PASS: DE-Berlin location.country={location.get('country')}")

    def test_listing_de_location_city(self, api_client, auth_headers):
        """location.city should be Berlin"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("city") == "Berlin", f"Expected city=Berlin, got {location.get('city')}"
        print(f"PASS: DE-Berlin location.city={location.get('city')}")

    def test_listing_de_location_district(self, api_client, auth_headers):
        """location.district should be Mitte"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("district") == "Mitte", f"Expected district=Mitte, got {location.get('district')}"
        print(f"PASS: DE-Berlin location.district={location.get('district')}")

    def test_listing_de_location_postal_code(self, api_client, auth_headers):
        """location.postal_code should be 10115"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("postal_code") == "10115", f"Expected postal_code=10115, got {location.get('postal_code')}"
        print(f"PASS: DE-Berlin location.postal_code={location.get('postal_code')}")

    def test_listing_de_location_lat_lng(self, api_client, auth_headers):
        """location.latitude and longitude should be set"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("latitude") is not None, "Expected latitude to be set"
        assert location.get("longitude") is not None, "Expected longitude to be set"
        print(f"PASS: DE-Berlin lat={location.get('latitude')}, lng={location.get('longitude')}")

    def test_listing_de_location_address_line(self, api_client, auth_headers):
        """location.address_line should be set"""
        listing_id = "8edea369-d74f-4638-aeec-0fe314fafb79"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("address_line") is not None and len(location.get("address_line", "")) > 0, "Expected address_line to be set"
        print(f"PASS: DE-Berlin location.address_line={location.get('address_line')}")


class TestDBAssertionsFRParis:
    """Verify DB persistence for FR-Paris listing"""

    def test_listing_fr_exists(self, api_client, auth_headers):
        """Listing b356e36b-5912-467a-996f-5017f63784a2 should exist"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: FR-Paris listing {listing_id} exists")

    def test_listing_fr_location_country(self, api_client, auth_headers):
        """location.country should be FR"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("country") == "FR", f"Expected country=FR, got {location.get('country')}"
        print(f"PASS: FR-Paris location.country={location.get('country')}")

    def test_listing_fr_location_city(self, api_client, auth_headers):
        """location.city should be Île-de-France"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("city") == "Île-de-France", f"Expected city=Île-de-France, got {location.get('city')}"
        print(f"PASS: FR-Paris location.city={location.get('city')}")

    def test_listing_fr_location_district(self, api_client, auth_headers):
        """location.district should be Paris"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("district") == "Paris", f"Expected district=Paris, got {location.get('district')}"
        print(f"PASS: FR-Paris location.district={location.get('district')}")

    def test_listing_fr_location_postal_code(self, api_client, auth_headers):
        """location.postal_code should be 75001"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("postal_code") == "75001", f"Expected postal_code=75001, got {location.get('postal_code')}"
        print(f"PASS: FR-Paris location.postal_code={location.get('postal_code')}")

    def test_listing_fr_location_lat_lng(self, api_client, auth_headers):
        """location.latitude and longitude should be set"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("latitude") is not None, "Expected latitude to be set"
        assert location.get("longitude") is not None, "Expected longitude to be set"
        print(f"PASS: FR-Paris lat={location.get('latitude')}, lng={location.get('longitude')}")

    def test_listing_fr_location_address_line(self, api_client, auth_headers):
        """location.address_line should be set"""
        listing_id = "b356e36b-5912-467a-996f-5017f63784a2"
        response = api_client.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=auth_headers)
        data = response.json()
        location = data.get("item", {}).get("location", {})
        assert location.get("address_line") is not None and len(location.get("address_line", "")) > 0, "Expected address_line to be set"
        print(f"PASS: FR-Paris location.address_line={location.get('address_line')}")


class TestAcceptanceReportConsistency:
    """Verify acceptance report claims match live data"""

    def test_report_files_exist(self):
        """p0_03_maps_acceptance.json and p0_03_maps_db_assertions.json should exist"""
        acceptance_path = "/app/test_reports/p0_03_maps_acceptance.json"
        db_assertions_path = "/app/test_reports/p0_03_maps_db_assertions.json"
        
        assert os.path.exists(acceptance_path), f"Acceptance report not found: {acceptance_path}"
        assert os.path.exists(db_assertions_path), f"DB assertions report not found: {db_assertions_path}"
        print("PASS: Both acceptance report files exist")

    def test_acceptance_report_maps_flow_pass(self):
        """Acceptance report should claim maps_flow_pass=true"""
        with open("/app/test_reports/p0_03_maps_acceptance.json", "r") as f:
            data = json.load(f)
        
        summary = data.get("summary", {})
        assert summary.get("maps_flow_pass") is True, f"Expected maps_flow_pass=True, got {summary.get('maps_flow_pass')}"
        assert summary.get("maps_api_key_active") is True, f"Expected maps_api_key_active=True, got {summary.get('maps_api_key_active')}"
        assert summary.get("cities_passed") == 3, f"Expected cities_passed=3, got {summary.get('cities_passed')}"
        print(f"PASS: Acceptance report summary matches - maps_flow_pass={summary.get('maps_flow_pass')}, cities_passed={summary.get('cities_passed')}")

    def test_acceptance_report_no_provider_errors(self):
        """Acceptance report should have 0 provider 4xx/5xx errors"""
        with open("/app/test_reports/p0_03_maps_acceptance.json", "r") as f:
            data = json.load(f)
        
        summary = data.get("summary", {})
        assert summary.get("provider_quota_or_auth_error_count") == 0, f"Expected 0 provider errors, got {summary.get('provider_quota_or_auth_error_count')}"
        assert summary.get("places_lookup_4xx5xx_count") == 0, f"Expected 0 places 4xx/5xx, got {summary.get('places_lookup_4xx5xx_count')}"
        print("PASS: No provider 4xx/5xx errors in acceptance report")

    def test_db_assertions_all_fields_populated(self):
        """DB assertions report should claim all_required_fields_populated=true"""
        with open("/app/test_reports/p0_03_maps_db_assertions.json", "r") as f:
            data = json.load(f)
        
        summary = data.get("summary", {})
        assert summary.get("all_required_fields_populated") is True, f"Expected all_required_fields_populated=True, got {summary.get('all_required_fields_populated')}"
        assert summary.get("rows") == 3, f"Expected rows=3, got {summary.get('rows')}"
        print(f"PASS: DB assertions summary - all_required_fields_populated={summary.get('all_required_fields_populated')}, rows={summary.get('rows')}")

    def test_db_assertions_no_missing_fields(self):
        """DB assertions report should have 0 missing fields for all rows"""
        with open("/app/test_reports/p0_03_maps_db_assertions.json", "r") as f:
            data = json.load(f)
        
        rows = data.get("rows", [])
        for row in rows:
            label = row.get("label")
            missing_count = row.get("required_field_missing_count", 0)
            missing_fields = row.get("missing_fields", [])
            assert missing_count == 0, f"{label}: Expected 0 missing fields, got {missing_count}"
            assert len(missing_fields) == 0, f"{label}: Expected no missing fields, got {missing_fields}"
            print(f"PASS: {label} has 0 missing fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
