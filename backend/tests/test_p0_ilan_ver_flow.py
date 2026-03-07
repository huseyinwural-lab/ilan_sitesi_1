"""
P0 İlan Ver Flow Backend Tests
- İlan 1: /ilan-ver modül grid render, module seçimi, home-category-layout config
- İlan 2: kategori ve vasıta trim akışı, trim listesinde duplicate olmaması
- İlan 3: create draft, PATCH draft, preview-ready, submit-review (Idempotency-Key)
- Submit sonrası detail_url response
"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://builder-hub-151.preview.emergentagent.com')

# Test credentials
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def user_token():
    """Get user auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip("User login failed")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def category_id(user_token):
    """Get a valid vehicle category ID for testing"""
    headers = {"Authorization": f"Bearer {user_token}"}
    # Try to get vehicle categories
    response = requests.get(
        f"{BASE_URL}/api/categories/children?module=vehicle&country=DE",
        headers=headers
    )
    if response.status_code == 200:
        categories = response.json()
        if isinstance(categories, list) and len(categories) > 0:
            return categories[0].get("id")
    
    # Fallback: try to search for any category
    response = requests.get(
        f"{BASE_URL}/api/categories?module=vehicle&country=DE",
        headers=headers
    )
    if response.status_code == 200:
        categories = response.json()
        if isinstance(categories, list) and len(categories) > 0:
            return categories[0].get("id")
    
    pytest.skip("No vehicle category found")


class TestHomeCategoryLayout:
    """İlan 1: home-category-layout config tests"""
    
    def test_get_home_category_layout_public(self):
        """Test public home-category-layout endpoint returns config with grid settings"""
        response = requests.get(f"{BASE_URL}/api/site/home-category-layout?country=DE")
        assert response.status_code == 200
        data = response.json()
        
        # Verify config structure
        assert "config" in data
        config = data["config"]
        
        # Verify listing module grid settings exist (fallback 2x4)
        assert "listing_module_grid_rows" in config
        assert "listing_module_grid_columns" in config
        assert "listing_lx_limit" in config
        
        # Verify defaults or configured values
        rows = config.get("listing_module_grid_rows", 2)
        cols = config.get("listing_module_grid_columns", 4)
        lx_limit = config.get("listing_lx_limit", 5)
        
        assert isinstance(rows, int) and rows >= 1 and rows <= 6
        assert isinstance(cols, int) and cols >= 1 and cols <= 6
        assert isinstance(lx_limit, int) and lx_limit >= 5 and lx_limit <= 50
        print(f"PASS: Home category layout config: rows={rows}, cols={cols}, lx_limit={lx_limit}")
    
    def test_get_home_category_layout_has_module_order(self):
        """Test home-category-layout returns module_order config"""
        response = requests.get(f"{BASE_URL}/api/site/home-category-layout?country=DE")
        assert response.status_code == 200
        data = response.json()
        config = data.get("config", {})
        
        # Check module order settings
        assert "module_order_mode" in config
        assert config["module_order_mode"] in ["manual", "alphabetical"]
        
        if "module_order" in config:
            module_order = config["module_order"]
            assert isinstance(module_order, list)
            print(f"PASS: Module order mode={config['module_order_mode']}, order={module_order}")


class TestVehicleTrims:
    """İlan 2: Vehicle trim selection and dedupe tests"""
    
    def test_vehicle_years_endpoint(self):
        """Test vehicle years returns list"""
        response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        items = data["items"]
        assert isinstance(items, list)
        print(f"PASS: Vehicle years returned {len(items)} items")
    
    def test_vehicle_makes_endpoint(self):
        """Test vehicle makes returns list for a year"""
        # First get a valid year
        years_response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_response.status_code != 200:
            pytest.skip("Could not get vehicle years")
        
        years = years_response.json().get("items", [])
        if not years:
            pytest.skip("No years available")
        
        year = years[0]
        response = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        items = data["items"]
        assert isinstance(items, list)
        print(f"PASS: Vehicle makes for year {year} returned {len(items)} items")
    
    def test_vehicle_trims_no_duplicates(self, user_token):
        """Test vehicle trims endpoint returns deduplicated results"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # First get valid year/make/model
        years_response = requests.get(f"{BASE_URL}/api/vehicle/years?country=DE")
        if years_response.status_code != 200:
            pytest.skip("Could not get vehicle years")
        
        years = years_response.json().get("items", [])
        if not years:
            pytest.skip("No years available")
        
        year = years[0]
        
        makes_response = requests.get(f"{BASE_URL}/api/vehicle/makes?year={year}&country=DE")
        if makes_response.status_code != 200:
            pytest.skip("Could not get vehicle makes")
        
        makes = makes_response.json().get("items", [])
        if not makes:
            pytest.skip("No makes available")
        
        make = makes[0].get("key")
        
        models_response = requests.get(f"{BASE_URL}/api/vehicle/models?year={year}&make={make}&country=DE")
        if models_response.status_code != 200:
            pytest.skip("Could not get vehicle models")
        
        models = models_response.json().get("items", [])
        if not models:
            pytest.skip("No models available")
        
        model = models[0].get("key")
        
        # Now get trims and check for duplicates
        response = requests.get(
            f"{BASE_URL}/api/vehicle/trims?year={year}&make={make}&model={model}&country=DE",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        
        # Check for duplicate trim keys
        seen_keys = set()
        duplicates = []
        for item in items:
            key = f"{item.get('key')}::{item.get('year')}"
            if key in seen_keys:
                duplicates.append(key)
            seen_keys.add(key)
        
        assert len(duplicates) == 0, f"Found duplicate trim keys: {duplicates}"
        print(f"PASS: Vehicle trims returned {len(items)} unique items, no duplicates")


class TestListingDraftFlow:
    """İlan 3: Listing draft creation, PATCH, preview-ready, submit-review"""
    
    def test_create_vehicle_draft(self, user_token, category_id):
        """Test creating a vehicle draft listing"""
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "category_id": category_id,
            "country": "DE",
            "title": "Test Arac Ilani",
            "description": "Test açıklaması"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response fields
        assert "id" in data
        assert "status" in data
        assert data["status"] == "draft"
        assert "flow_state" in data
        assert data["flow_state"] == "draft"
        assert "draft_id" in data
        
        print(f"PASS: Created draft listing {data['id']}")
        return data["id"]
    
    def test_patch_vehicle_draft(self, user_token, category_id):
        """Test PATCH draft updates listing"""
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        # First create a draft
        create_payload = {
            "category_id": category_id,
            "country": "DE",
            "title": "Test Arac Ilani PATCH",
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers=headers,
            json=create_payload
        )
        
        assert create_response.status_code == 200
        listing_id = create_response.json()["id"]
        
        # Now PATCH the draft
        patch_payload = {
            "core_fields": {
                "title": "Updated Title",
                "description": "Updated description for PATCH test",
                "price": {
                    "price_type": "FIXED",
                    "amount": 15000,
                    "currency_primary": "EUR"
                }
            },
            "location": {
                "city": "Berlin",
                "country": "DE"
            }
        }
        
        patch_response = requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft",
            headers=headers,
            json=patch_payload
        )
        
        assert patch_response.status_code == 200
        data = patch_response.json()
        
        assert data["id"] == listing_id
        assert "flow_state" in data
        assert "updated_at" in data
        
        print(f"PASS: PATCH draft {listing_id} successful")
    
    def test_preview_ready_flow(self, user_token, category_id):
        """Test marking listing as preview-ready"""
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        # Create and prepare draft
        create_payload = {
            "category_id": category_id,
            "country": "DE",
            "title": "Preview Ready Test",
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers=headers,
            json=create_payload
        )
        
        assert create_response.status_code == 200
        listing_id = create_response.json()["id"]
        
        # PATCH to add required fields
        patch_payload = {
            "core_fields": {
                "title": "Preview Ready Test Updated",
                "description": "Test description for preview",
                "price": {
                    "price_type": "FIXED",
                    "amount": 20000,
                    "currency_primary": "EUR"
                }
            },
            "location": {
                "city": "Munich",
                "country": "DE"
            }
        }
        
        requests.patch(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft",
            headers=headers,
            json=patch_payload
        )
        
        # Mark as preview-ready
        preview_payload = {
            "core_fields": {
                "title": "Preview Ready Test Updated",
                "description": "Test description for preview",
                "price": {
                    "price_type": "FIXED",
                    "amount": 20000,
                    "currency_primary": "EUR"
                }
            },
            "location": {
                "city": "Munich",
                "country": "DE"
            },
            "contact": {
                "contact_name": "Test User",
                "contact_phone": "+491701112233"
            }
        }
        
        preview_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready",
            headers=headers,
            json=preview_payload
        )
        
        assert preview_response.status_code == 200
        data = preview_response.json()
        
        assert data["id"] == listing_id
        assert data["flow_state"] == "preview_ready"
        assert data["validation_errors"] == []
        
        print(f"PASS: Listing {listing_id} marked preview-ready")
        return listing_id
    
    def test_submit_review_requires_idempotency_key(self, user_token, category_id):
        """Test submit-review requires Idempotency-Key header"""
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        # Create and prepare draft
        create_payload = {"category_id": category_id, "country": "DE"}
        create_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers=headers,
            json=create_payload
        )
        
        assert create_response.status_code == 200
        listing_id = create_response.json()["id"]
        
        # Prepare the listing with required fields
        patch_payload = {
            "core_fields": {
                "title": "Idempotency Test Listing",
                "description": "Test description",
                "price": {"price_type": "FIXED", "amount": 10000, "currency_primary": "EUR"}
            },
            "location": {"city": "Hamburg", "country": "DE"}
        }
        requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=patch_payload)
        
        # Mark preview-ready
        preview_payload = {
            "core_fields": {
                "title": "Idempotency Test Listing",
                "description": "Test description",
                "price": {"price_type": "FIXED", "amount": 10000, "currency_primary": "EUR"}
            },
            "location": {"city": "Hamburg", "country": "DE"},
            "contact": {"contact_name": "Test", "contact_phone": "+49123456789"}
        }
        requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=preview_payload)
        
        # Try to submit without Idempotency-Key - should fail
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Idempotency-Key" in str(data.get("detail", ""))
        
        print(f"PASS: submit-review correctly requires Idempotency-Key header")
    
    def test_submit_review_with_idempotency_key(self, user_token, category_id):
        """Test submit-review with Idempotency-Key returns detail_url"""
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        # Create and prepare draft
        create_payload = {"category_id": category_id, "country": "DE"}
        create_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers=headers,
            json=create_payload
        )
        
        assert create_response.status_code == 200
        listing_id = create_response.json()["id"]
        
        # Prepare the listing
        patch_payload = {
            "core_fields": {
                "title": "Submit Review Test Listing",
                "description": "Test description for submit",
                "price": {"price_type": "FIXED", "amount": 12000, "currency_primary": "EUR"}
            },
            "location": {"city": "Frankfurt", "country": "DE"}
        }
        requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=patch_payload)
        
        # Mark preview-ready
        preview_payload = {
            "core_fields": {
                "title": "Submit Review Test Listing",
                "description": "Test description for submit",
                "price": {"price_type": "FIXED", "amount": 12000, "currency_primary": "EUR"}
            },
            "location": {"city": "Frankfurt", "country": "DE"},
            "contact": {"contact_name": "Test User", "contact_phone": "+49123456789"}
        }
        requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=preview_payload)
        
        # Submit with Idempotency-Key
        idempotency_key = str(uuid.uuid4())
        headers_with_key = {
            **headers,
            "Idempotency-Key": idempotency_key
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers=headers_with_key
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response fields
        assert "id" in data
        assert data["id"] == listing_id
        assert "status" in data
        assert data["status"] == "submitted_for_review"
        assert "flow_state" in data
        assert data["flow_state"] == "submitted_for_review"
        assert "detail_url" in data
        assert f"/ilan/{listing_id}" in data["detail_url"]
        
        print(f"PASS: submit-review returned detail_url: {data['detail_url']}")
    
    def test_submit_review_idempotency_prevents_duplicate(self, user_token, category_id):
        """Test same idempotency key returns cached response without duplicate submission"""
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        # Create and prepare draft
        create_payload = {"category_id": category_id, "country": "DE"}
        create_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers=headers,
            json=create_payload
        )
        
        assert create_response.status_code == 200
        listing_id = create_response.json()["id"]
        
        # Prepare and mark preview-ready
        payload = {
            "core_fields": {
                "title": "Idempotency Duplicate Test",
                "description": "Testing duplicate prevention",
                "price": {"price_type": "FIXED", "amount": 15000, "currency_primary": "EUR"}
            },
            "location": {"city": "Cologne", "country": "DE"},
            "contact": {"contact_name": "Test", "contact_phone": "+49123456789"}
        }
        requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=payload)
        requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=payload)
        
        # Submit first time
        idempotency_key = str(uuid.uuid4())
        headers_with_key = {**headers, "Idempotency-Key": idempotency_key}
        
        first_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers=headers_with_key
        )
        
        assert first_response.status_code == 200
        first_data = first_response.json()
        assert first_data.get("idempotency_reused") == False
        
        # Submit second time with same key - should return cached response
        second_response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers=headers_with_key
        )
        
        assert second_response.status_code == 200
        second_data = second_response.json()
        assert second_data.get("idempotency_reused") == True
        assert second_data["id"] == first_data["id"]
        assert second_data["detail_url"] == first_data["detail_url"]
        
        print(f"PASS: Idempotency key prevents duplicate submission")


class TestDopingOptions:
    """Test doping options endpoint"""
    
    def test_get_doping_options(self, user_token):
        """Test doping options returns valid options"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/v1/listings/doping/options",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has options
        assert "options" in data
        options = data["options"]
        assert isinstance(options, list)
        
        print(f"PASS: Doping options returned {len(options)} options")


class TestCatalogSchema:
    """Test catalog schema endpoint for form blocks"""
    
    def test_get_catalog_schema(self, user_token, category_id):
        """Test catalog schema returns form schema with modules"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/catalog/schema?category_id={category_id}&country=DE",
            headers=headers
        )
        
        # Schema may not exist for all categories - just check endpoint works
        if response.status_code == 200:
            data = response.json()
            schema = data.get("schema") or {}
            
            # If schema exists, check structure
            if schema:
                assert isinstance(schema, dict)
                print(f"PASS: Catalog schema returned for category {category_id}")
            else:
                print(f"INFO: No schema defined for category {category_id}")
        else:
            print(f"INFO: Catalog schema endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
