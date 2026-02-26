"""
Vehicle Selector Wizard P0 Tests
Testing: Year→Make→Model→Trim chain selection and validation rules

Test Scenarios:
1. Backend Draft API - Vehicle payload validation for year>=2000 (trim required)
2. Backend Draft API - Vehicle payload validation for year<2000 (manual trim required)
3. Backend Draft API - Chain reset behavior (clear downstream fields)
4. Backend Draft API - 422 error responses for validation failures
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://theme-config-api.preview.emergentagent.com").rstrip("/")

# Test credentials
TEST_USER_EMAIL = "user@platform.com"
TEST_USER_PASSWORD = "User123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


class TestAuth:
    """Authentication helper"""
    
    @staticmethod
    def get_user_token():
        """Get access token for test user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    @staticmethod
    def get_admin_token():
        """Get access token for admin"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None


class TestVehicleSelectorAPI:
    """Test Vehicle Selector Chain API endpoints"""
    
    def test_get_years_returns_list(self):
        """GET /api/vehicle/years should return years list"""
        response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should have items field"
        assert isinstance(data["items"], list), "items should be a list"
        print(f"✓ Years API returned {len(data['items'])} years")
    
    def test_get_makes_returns_list_for_year(self):
        """GET /api/vehicle/makes should return makes for given year"""
        # First get available years
        years_response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        years = years_response.json().get("items", [])
        if not years:
            pytest.skip("No years available")
        
        test_year = years[0]  # Use first available year
        response = requests.get(f"{BASE_URL}/api/vehicle/makes?year={test_year}&country=DE")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should have items field"
        print(f"✓ Makes API returned {len(data['items'])} makes for year {test_year}")
    
    def test_get_models_returns_list_for_make(self):
        """GET /api/vehicle/models should return models for given year+make"""
        # Get years, then makes
        years_response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        years = years_response.json().get("items", [])
        if not years:
            pytest.skip("No years available")
        
        test_year = years[0]
        makes_response = requests.get(f"{BASE_URL}/api/vehicle/makes?year={test_year}&country=DE")
        makes = makes_response.json().get("items", [])
        if not makes:
            pytest.skip("No makes available for year")
        
        test_make = makes[0].get("key") or makes[0].get("name")
        response = requests.get(f"{BASE_URL}/api/vehicle/models?year={test_year}&make={test_make}&country=DE")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should have items field"
        print(f"✓ Models API returned {len(data['items'])} models for year={test_year}, make={test_make}")
    
    def test_get_options_returns_filter_values(self):
        """GET /api/vehicle/options should return fuel_types, bodies, transmissions, drives, engine_types"""
        # Chain: years -> makes -> models
        years_response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        years = years_response.json().get("items", [])
        if not years:
            pytest.skip("No years available")
        
        test_year = years[0]
        makes_response = requests.get(f"{BASE_URL}/api/vehicle/makes?year={test_year}&country=DE")
        makes = makes_response.json().get("items", [])
        if not makes:
            pytest.skip("No makes available")
        
        test_make = makes[0].get("key") or makes[0].get("name")
        models_response = requests.get(f"{BASE_URL}/api/vehicle/models?year={test_year}&make={test_make}&country=DE")
        models = models_response.json().get("items", [])
        if not models:
            pytest.skip("No models available")
        
        test_model = models[0].get("key") or models[0].get("name")
        response = requests.get(
            f"{BASE_URL}/api/vehicle/options?year={test_year}&make={test_make}&model={test_model}&country=DE"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        options = data.get("options", {})
        expected_keys = ["fuel_types", "bodies", "transmissions", "drives", "engine_types"]
        for key in expected_keys:
            assert key in options, f"Missing key: {key}"
        print(f"✓ Options API returned filters for year={test_year}, make={test_make}, model={test_model}")
    
    def test_get_trims_returns_list(self):
        """GET /api/vehicle/trims should return trims list"""
        # Get chain first
        years_response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        years = years_response.json().get("items", [])
        if not years:
            pytest.skip("No years available")
        
        test_year = years[0]
        makes_response = requests.get(f"{BASE_URL}/api/vehicle/makes?year={test_year}&country=DE")
        makes = makes_response.json().get("items", [])
        if not makes:
            pytest.skip("No makes available")
        
        test_make = makes[0].get("key") or makes[0].get("name")
        models_response = requests.get(f"{BASE_URL}/api/vehicle/models?year={test_year}&make={test_make}&country=DE")
        models = models_response.json().get("items", [])
        if not models:
            pytest.skip("No models available")
        
        test_model = models[0].get("key") or models[0].get("name")
        response = requests.get(
            f"{BASE_URL}/api/vehicle/trims?year={test_year}&make={test_make}&model={test_model}&country=DE"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should have items field"
        print(f"✓ Trims API returned {len(data['items'])} trims")


class TestDraftVehicleValidation:
    """Test Draft API vehicle payload validation rules"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create draft listing"""
        self.token = TestAuth.get_user_token()
        if not self.token:
            pytest.skip("Failed to get user token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.draft_id = None
    
    def _create_draft(self):
        """Create a draft listing for testing"""
        # Get category first - use /api/categories endpoint with module=vehicle
        categories_resp = requests.get(f"{BASE_URL}/api/categories?module=vehicle&country=DE")
        if categories_resp.status_code != 200:
            pytest.skip(f"Could not get categories: {categories_resp.status_code} {categories_resp.text}")
        
        categories = categories_resp.json()
        # Find a leaf category (hierarchy_complete=True)
        cat_id = None
        for cat in categories:
            if cat.get("hierarchy_complete"):
                cat_id = cat.get("id")
                break
        
        if not cat_id:
            pytest.skip("No complete category found")
        
        create_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            json={"country": "DE", "category_key": cat_id, "category_id": cat_id},
            headers=self.headers
        )
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create draft: {create_response.text}")
        
        self.draft_id = create_response.json().get("id")
        return self.draft_id
    
    def test_year_gte_2000_requires_trim_id(self):
        """year >= 2000 için vehicle_trim_id zorunludur - should return 422"""
        draft_id = self._create_draft()
        
        # Try to save vehicle with year >= 2000 but no trim_id
        payload = {
            "vehicle": {
                "make_key": "bmw",
                "make_id": str(uuid.uuid4()),
                "model_key": "3-series",
                "model_id": str(uuid.uuid4()),
                "year": 2020,
                "vehicle_trim_id": None,  # Missing trim
                "manual_trim_flag": False,
                "manual_trim_text": None
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 422, f"Expected 422 for year>=2000 without trim, got {response.status_code}: {response.text}"
        detail = response.json().get("detail", "")
        assert "trim" in detail.lower() or "2000" in detail, f"Error should mention trim requirement: {detail}"
        print(f"✓ Backend correctly rejected year>=2000 without trim_id: {detail}")
    
    def test_year_lt_2000_requires_manual_trim(self):
        """year < 2000 için manual_trim_flag=true ve manual_trim_text zorunludur - should return 422"""
        draft_id = self._create_draft()
        
        # Try to save vehicle with year < 2000 without manual trim
        payload = {
            "vehicle": {
                "make_key": "bmw",
                "make_id": str(uuid.uuid4()),
                "model_key": "3-series",
                "model_id": str(uuid.uuid4()),
                "year": 1995,
                "vehicle_trim_id": None,
                "manual_trim_flag": False,  # Missing manual flag
                "manual_trim_text": None
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 422, f"Expected 422 for year<2000 without manual_trim_flag, got {response.status_code}: {response.text}"
        detail = response.json().get("detail", "")
        assert "manual" in detail.lower() or "2000" in detail, f"Error should mention manual trim requirement: {detail}"
        print(f"✓ Backend correctly rejected year<2000 without manual_trim_flag: {detail}")
    
    def test_year_lt_2000_manual_trim_text_too_short(self):
        """year < 2000 manual_trim_text must be at least 2 chars - should return 422"""
        draft_id = self._create_draft()
        
        # Try to save vehicle with year < 2000 with short manual text
        payload = {
            "vehicle": {
                "make_key": "bmw",
                "make_id": str(uuid.uuid4()),
                "model_key": "3-series", 
                "model_id": str(uuid.uuid4()),
                "year": 1995,
                "vehicle_trim_id": None,
                "manual_trim_flag": True,
                "manual_trim_text": "X"  # Too short (< 2 chars)
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 422, f"Expected 422 for short manual_trim_text, got {response.status_code}: {response.text}"
        detail = response.json().get("detail", "")
        print(f"✓ Backend correctly rejected short manual_trim_text: {detail}")
    
    def test_year_lt_2000_valid_manual_trim_succeeds(self):
        """year < 2000 with valid manual_trim should succeed"""
        draft_id = self._create_draft()
        
        # Save vehicle with year < 2000 and valid manual trim
        payload = {
            "vehicle": {
                "make_key": "bmw",
                "make_id": str(uuid.uuid4()),
                "model_key": "3-series",
                "model_id": str(uuid.uuid4()),
                "year": 1995,
                "vehicle_trim_id": None,
                "manual_trim_flag": True,
                "manual_trim_text": "Classic 2.0"  # Valid manual text
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200 for valid manual trim, got {response.status_code}: {response.text}"
        print(f"✓ Backend accepted year<2000 with valid manual trim")
        
        # Verify the saved data via GET
        get_response = requests.get(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            headers=self.headers
        )
        assert get_response.status_code == 200
        item = get_response.json().get("item", {})
        vehicle = item.get("vehicle") or item.get("attributes", {}).get("vehicle", {})
        assert vehicle.get("manual_trim_flag") == True, "manual_trim_flag should be True"
        assert vehicle.get("manual_trim_text") == "Classic 2.0", "manual_trim_text should be saved"
        assert vehicle.get("vehicle_trim_id") is None, "vehicle_trim_id should be None for manual"
        print(f"✓ Verified saved manual trim data")
    
    def test_year_gte_2000_valid_trim_id_succeeds(self):
        """year >= 2000 with valid trim_id should succeed"""
        draft_id = self._create_draft()
        
        # Get actual trim_id from API
        years_resp = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        years = years_resp.json().get("items", [])
        # Find a year >= 2000
        test_year = None
        for y in years:
            if int(y) >= 2000:
                test_year = int(y)
                break
        
        if not test_year:
            pytest.skip("No years >= 2000 available")
        
        makes_resp = requests.get(f"{BASE_URL}/api/vehicle/makes?year={test_year}&country=DE")
        makes = makes_resp.json().get("items", [])
        if not makes:
            pytest.skip("No makes for year")
        
        test_make = makes[0]
        make_key = test_make.get("key")
        make_id = test_make.get("id")
        
        models_resp = requests.get(f"{BASE_URL}/api/vehicle/models?year={test_year}&make={make_key}&country=DE")
        models = models_resp.json().get("items", [])
        if not models:
            pytest.skip("No models for make")
        
        test_model = models[0]
        model_key = test_model.get("key")
        model_id = test_model.get("id")
        
        trims_resp = requests.get(
            f"{BASE_URL}/api/vehicle/trims?year={test_year}&make={make_key}&model={model_key}&country=DE"
        )
        trims = trims_resp.json().get("items", [])
        if not trims:
            pytest.skip("No trims available")
        
        test_trim = trims[0]
        trim_id = test_trim.get("id")
        trim_key = test_trim.get("key")
        
        # Save with valid trim_id
        payload = {
            "vehicle": {
                "make_key": make_key,
                "make_id": make_id,
                "model_key": model_key,
                "model_id": model_id,
                "year": test_year,
                "vehicle_trim_id": trim_id,
                "trim_key": trim_key,
                "manual_trim_flag": False,
                "manual_trim_text": None
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            json=payload,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Expected 200 for valid trim_id, got {response.status_code}: {response.text}"
        print(f"✓ Backend accepted year>={test_year} with valid trim_id={trim_id}")
        
        # Verify saved data
        get_response = requests.get(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            headers=self.headers
        )
        assert get_response.status_code == 200
        item = get_response.json().get("item", {})
        vehicle = item.get("vehicle") or item.get("attributes", {}).get("vehicle", {})
        assert vehicle.get("vehicle_trim_id") == trim_id or vehicle.get("trim_id") == trim_id, "trim_id should be saved"
        assert vehicle.get("manual_trim_flag") == False, "manual_trim_flag should be False"
        print(f"✓ Verified saved trim_id data")


class TestDraftVehicleChainReset:
    """Test that changing parent field resets child fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.token = TestAuth.get_user_token()
        if not self.token:
            pytest.skip("Failed to get user token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_reset_on_make_change(self):
        """When make changes, model/year/trim should be clearable"""
        # This tests the frontend's reset behavior via backend draft save
        # After changing make, we should be able to save with null model/year/trim
        
        # Get categories and create draft
        categories_resp = requests.get(f"{BASE_URL}/api/categories?module=vehicle&country=DE")
        if categories_resp.status_code != 200:
            pytest.skip(f"Could not get categories: {categories_resp.text}")
        
        categories = categories_resp.json()
        cat_id = None
        for cat in categories:
            if cat.get("hierarchy_complete"):
                cat_id = cat.get("id")
                break
        
        if not cat_id:
            pytest.skip("No complete category found")
        
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            json={"country": "DE", "category_key": cat_id, "category_id": cat_id},
            headers=self.headers
        )
        if create_resp.status_code not in [200, 201]:
            pytest.skip(f"Could not create draft: {create_resp.text}")
        
        draft_id = create_resp.json().get("id")
        
        # Save with all fields cleared except make
        payload = {
            "vehicle": {
                "make_key": "audi",
                "make_id": None,  # UUID would be here in real flow
                "model_key": None,
                "model_id": None,
                "year": None,
                "vehicle_trim_id": None,
                "manual_trim_flag": False,
                "manual_trim_text": None
            }
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{draft_id}/draft",
            json=payload,
            headers=self.headers
        )
        
        # This should succeed (no validation when year is null)
        assert response.status_code == 200, f"Expected 200 for partial save, got {response.status_code}: {response.text}"
        print(f"✓ Backend allows partial vehicle save (make only, no year)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
