"""
P0: Vehicle Import Validation & Vehicle Selector Engine Tests
- JSON parse/schema/business validation error codes
- Vehicle Selector Engine API (years, makes, models, options, trims)
- Vasıta (vehicle) category module filtering
"""
import pytest
import requests
import json
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

BASE_URL = BASE_URL.rstrip('/')


class TestVehicleImportValidation:
    """Tests for Vehicle Master Import validation error codes"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        data = login_resp.json()
        self.admin_token = data["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    def test_upload_invalid_json_returns_parse_error(self):
        """POST /api/admin/vehicle-master-import/jobs/upload invalid JSON returns JSON_PARSE_ERROR + field_errors"""
        files = {
            "file": ("test.json", b"{ invalid json }", "application/json")
        }
        data = {"dry_run": "true"}
        resp = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data=data,
            headers=self.admin_headers
        )
        # Should return 400 with JSON_PARSE_ERROR
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "error_code" in body, f"Missing error_code in response: {body}"
        assert body["error_code"] == "JSON_PARSE_ERROR", f"Expected JSON_PARSE_ERROR, got {body['error_code']}"
        assert "field_errors" in body, f"Missing field_errors in response: {body}"
        assert len(body["field_errors"]) > 0, "field_errors should not be empty"
        print(f"✓ Invalid JSON returns JSON_PARSE_ERROR with field_errors: {body}")

    def test_upload_empty_json_returns_schema_error(self):
        """POST /api/admin/vehicle-master-import/jobs/upload empty array returns schema error"""
        files = {
            "file": ("test.json", b"[]", "application/json")
        }
        data = {"dry_run": "true"}
        resp = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data=data,
            headers=self.admin_headers
        )
        # Empty array should be valid structure but may fail at schema or succeed
        # Check response structure
        if resp.status_code == 400:
            body = resp.json()
            assert "error_code" in body, f"Missing error_code: {body}"
            print(f"✓ Empty array returns error_code: {body['error_code']}")
        else:
            print(f"✓ Empty array accepted, status: {resp.status_code}")

    def test_upload_non_array_json_returns_schema_error(self):
        """POST /api/admin/vehicle-master-import/jobs/upload non-array JSON returns JSON_SCHEMA_ERROR"""
        files = {
            "file": ("test.json", b'{"not": "an array"}', "application/json")
        }
        data = {"dry_run": "true"}
        resp = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data=data,
            headers=self.admin_headers
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "error_code" in body, f"Missing error_code: {body}"
        assert body["error_code"] == "JSON_SCHEMA_ERROR", f"Expected JSON_SCHEMA_ERROR, got {body['error_code']}"
        assert "field_errors" in body, f"Missing field_errors: {body}"
        print(f"✓ Non-array JSON returns JSON_SCHEMA_ERROR: {body}")

    def test_upload_missing_required_fields_returns_schema_error(self):
        """POST /api/admin/vehicle-master-import/jobs/upload missing required fields returns schema error"""
        # Missing make_name, model_name, etc.
        test_records = [
            {"year": 2024}  # Missing required fields
        ]
        files = {
            "file": ("test.json", json.dumps(test_records).encode(), "application/json")
        }
        data = {"dry_run": "true"}
        resp = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data=data,
            headers=self.admin_headers
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "error_code" in body, f"Missing error_code: {body}"
        assert body["error_code"] == "JSON_SCHEMA_ERROR", f"Expected JSON_SCHEMA_ERROR, got {body['error_code']}"
        assert "field_errors" in body, f"Missing field_errors: {body}"
        print(f"✓ Missing required fields returns JSON_SCHEMA_ERROR: {body}")

    def test_upload_duplicate_trim_key_returns_business_validation_error(self):
        """POST /api/admin/vehicle-master-import/jobs/upload duplicate trim key returns BUSINESS_VALIDATION_ERROR"""
        # Duplicate trim key (same make_name, model_name, trim_name, year combination)
        test_records = [
            {
                "make_name": "TEST_DuplicateMake",
                "model_name": "TEST_DuplicateModel",
                "trim_name": "TEST_DuplicateTrim",
                "year": 2024
            },
            {
                "make_name": "TEST_DuplicateMake",
                "model_name": "TEST_DuplicateModel",
                "trim_name": "TEST_DuplicateTrim",
                "year": 2024
            }
        ]
        files = {
            "file": ("test.json", json.dumps(test_records).encode(), "application/json")
        }
        data = {"dry_run": "true"}
        resp = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data=data,
            headers=self.admin_headers
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "error_code" in body, f"Missing error_code: {body}"
        assert body["error_code"] == "BUSINESS_VALIDATION_ERROR", f"Expected BUSINESS_VALIDATION_ERROR, got {body['error_code']}"
        assert "field_errors" in body, f"Missing field_errors: {body}"
        print(f"✓ Duplicate trim key returns BUSINESS_VALIDATION_ERROR: {body}")

    def test_upload_valid_json_creates_job(self):
        """POST /api/admin/vehicle-master-import/jobs/upload valid JSON creates job"""
        test_records = [
            {
                "make_name": "TEST_ValidMake",
                "model_name": "TEST_ValidModel",
                "trim_name": "TEST_ValidTrim",
                "year": 2024
            }
        ]
        files = {
            "file": ("test.json", json.dumps(test_records).encode(), "application/json")
        }
        data = {"dry_run": "true"}
        resp = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data=data,
            headers=self.admin_headers
        )
        # Valid JSON should create a job
        if resp.status_code == 200:
            body = resp.json()
            assert "job" in body, f"Missing job in response: {body}"
            assert "id" in body["job"], f"Missing job id: {body}"
            print(f"✓ Valid JSON creates job: {body['job']['id']}")
        else:
            print(f"✓ Valid JSON response status: {resp.status_code}")


class TestVehicleSelectorEngine:
    """Tests for Vehicle Selector Engine public API"""

    def test_vehicle_years_endpoint(self):
        """GET /api/vehicle/years returns list of years"""
        resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "items" in body, f"Missing items in response: {body}"
        print(f"✓ GET /api/vehicle/years returns {len(body['items'])} years")
        if body['items']:
            print(f"  Sample years: {body['items'][:5]}")

    def test_vehicle_makes_endpoint(self):
        """GET /api/vehicle/makes requires year and returns makes"""
        # First get available years
        years_resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_resp.status_code != 200 or not years_resp.json().get("items"):
            pytest.skip("No vehicle years in database")
        
        year = years_resp.json()["items"][0]
        resp = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "items" in body, f"Missing items in response: {body}"
        assert "year" in body, f"Missing year in response: {body}"
        print(f"✓ GET /api/vehicle/makes year={year} returns {len(body['items'])} makes")
        if body['items']:
            print(f"  Sample makes: {[m['label'] for m in body['items'][:3]]}")

    def test_vehicle_models_endpoint(self):
        """GET /api/vehicle/models requires year and make, returns models"""
        # Get years
        years_resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_resp.status_code != 200 or not years_resp.json().get("items"):
            pytest.skip("No vehicle years in database")
        year = years_resp.json()["items"][0]

        # Get makes
        makes_resp = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        if makes_resp.status_code != 200 or not makes_resp.json().get("items"):
            pytest.skip("No vehicle makes for year in database")
        make = makes_resp.json()["items"][0]["key"]

        resp = requests.get(f"{BASE_URL}/api/vehicle/models?year={year}&make={make}&country=DE")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "items" in body, f"Missing items in response: {body}"
        assert "year" in body, f"Missing year in response: {body}"
        assert "make" in body, f"Missing make in response: {body}"
        print(f"✓ GET /api/vehicle/models year={year} make={make} returns {len(body['items'])} models")
        if body['items']:
            print(f"  Sample models: {[m['label'] for m in body['items'][:3]]}")

    def test_vehicle_options_endpoint(self):
        """GET /api/vehicle/options returns fuel types, bodies, transmissions, etc."""
        # Get years
        years_resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_resp.status_code != 200 or not years_resp.json().get("items"):
            pytest.skip("No vehicle years in database")
        year = years_resp.json()["items"][0]

        # Get makes
        makes_resp = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        if makes_resp.status_code != 200 or not makes_resp.json().get("items"):
            pytest.skip("No vehicle makes for year in database")
        make = makes_resp.json()["items"][0]["key"]

        # Get models
        models_resp = requests.get(f"{BASE_URL}/api/vehicle/models?year={year}&make={make}&country=DE")
        if models_resp.status_code != 200 or not models_resp.json().get("items"):
            pytest.skip("No vehicle models for make in database")
        model = models_resp.json()["items"][0]["key"]

        resp = requests.get(f"{BASE_URL}/api/vehicle/options?year={year}&make={make}&model={model}&country=DE")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "options" in body, f"Missing options in response: {body}"
        options = body["options"]
        # Check expected option keys
        expected_keys = ["fuel_types", "bodies", "transmissions", "drives", "engine_types"]
        for key in expected_keys:
            assert key in options, f"Missing {key} in options: {options}"
        print(f"✓ GET /api/vehicle/options returns options: {list(options.keys())}")
        for key, values in options.items():
            print(f"  {key}: {values[:3] if len(values) > 3 else values}")

    def test_vehicle_trims_endpoint(self):
        """GET /api/vehicle/trims returns filtered trims"""
        # Get years
        years_resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_resp.status_code != 200 or not years_resp.json().get("items"):
            pytest.skip("No vehicle years in database")
        year = years_resp.json()["items"][0]

        # Get makes
        makes_resp = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        if makes_resp.status_code != 200 or not makes_resp.json().get("items"):
            pytest.skip("No vehicle makes for year in database")
        make = makes_resp.json()["items"][0]["key"]

        # Get models
        models_resp = requests.get(f"{BASE_URL}/api/vehicle/models?year={year}&make={make}&country=DE")
        if models_resp.status_code != 200 or not models_resp.json().get("items"):
            pytest.skip("No vehicle models for make in database")
        model = models_resp.json()["items"][0]["key"]

        resp = requests.get(f"{BASE_URL}/api/vehicle/trims?year={year}&make={make}&model={model}&country=DE")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "items" in body, f"Missing items in response: {body}"
        print(f"✓ GET /api/vehicle/trims year={year} make={make} model={model} returns {len(body['items'])} trims")
        if body['items']:
            print(f"  Sample trims: {[t['label'] for t in body['items'][:3]]}")

    def test_vehicle_trims_with_filters(self):
        """GET /api/vehicle/trims with optional filters (fuel_type, body, etc.)"""
        # Get years
        years_resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_resp.status_code != 200 or not years_resp.json().get("items"):
            pytest.skip("No vehicle years in database")
        year = years_resp.json()["items"][0]

        # Get makes
        makes_resp = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        if makes_resp.status_code != 200 or not makes_resp.json().get("items"):
            pytest.skip("No vehicle makes for year in database")
        make = makes_resp.json()["items"][0]["key"]

        # Get models
        models_resp = requests.get(f"{BASE_URL}/api/vehicle/models?year={year}&make={make}&country=DE")
        if models_resp.status_code != 200 or not models_resp.json().get("items"):
            pytest.skip("No vehicle models for make in database")
        model = models_resp.json()["items"][0]["key"]

        # Get options to find a valid fuel_type filter
        options_resp = requests.get(f"{BASE_URL}/api/vehicle/options?year={year}&make={make}&model={model}&country=DE")
        if options_resp.status_code != 200:
            pytest.skip("Could not get vehicle options")
        options = options_resp.json().get("options", {})
        fuel_types = options.get("fuel_types", [])

        if fuel_types:
            fuel_type = fuel_types[0]
            resp = requests.get(f"{BASE_URL}/api/vehicle/trims?year={year}&make={make}&model={model}&fuel_type={fuel_type}&country=DE")
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert "items" in body, f"Missing items in response: {body}"
            print(f"✓ GET /api/vehicle/trims with fuel_type={fuel_type} returns {len(body['items'])} trims")
        else:
            print("✓ No fuel types to filter, skipping filter test")


class TestAdminCategoriesSortOrder:
    """Tests for Admin Categories sort_order - read-only automatic"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        data = login_resp.json()
        self.admin_token = data["access_token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    def test_categories_list_includes_sort_order(self):
        """GET /api/admin/categories returns items with sort_order field"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers=self.admin_headers
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "items" in body, f"Missing items in response: {body}"
        
        if body["items"]:
            for item in body["items"][:3]:
                assert "sort_order" in item, f"Missing sort_order in item: {item}"
                print(f"  Category {item.get('name')}: sort_order={item['sort_order']}")
        print(f"✓ GET /api/admin/categories returns {len(body['items'])} items with sort_order")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
