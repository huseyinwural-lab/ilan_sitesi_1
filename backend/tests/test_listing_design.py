"""
Backend tests for İlan Tasarım (Listing Design) endpoints
Tests: GET/PUT /api/admin/site/listing-design and GET /api/site/listing-design
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json().get("access_token")


class TestAdminListingDesign:
    """Admin listing design endpoint tests"""
    
    def test_get_admin_listing_design(self, admin_token):
        """GET /api/admin/site/listing-design should return config"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/listing-design",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "config" in data, "Response should contain 'config' key"
        
        config = data["config"]
        # Verify step1 (module grid) structure
        assert "step1" in config, "Config should have 'step1'"
        assert "rows" in config["step1"], "step1 should have 'rows'"
        assert "columns" in config["step1"], "step1 should have 'columns'"
        assert "cards" in config["step1"], "step1 should have 'cards'"
        
        # Verify step2 (search/breadcrumb) structure
        assert "step2" in config, "Config should have 'step2'"
        assert "continue_limit" in config["step2"], "step2 should have 'continue_limit'"
        
        # Verify step3 (8 block form) structure
        assert "step3" in config, "Config should have 'step3'"
        assert "media" in config["step3"], "step3 should have 'media'"
        assert "contact" in config["step3"], "step3 should have 'contact'"
        assert "terms" in config["step3"], "step3 should have 'terms'"
        
        print(f"Admin listing design GET: OK - config has {len(config.get('step1', {}).get('cards', []))} cards")
    
    def test_put_admin_listing_design(self, admin_token):
        """PUT /api/admin/site/listing-design should update and return config"""
        update_payload = {
            "config": {
                "step1": {
                    "rows": 2,
                    "columns": 4,
                    "cards": [
                        {"id": "vehicle", "title": "Vasıta", "description": "Araç ilanı ver", "module_key": "vehicle", "border_color": "#2563eb", "image_url": ""},
                        {"id": "real_estate", "title": "Emlak", "description": "Emlak ilanı ver", "module_key": "real_estate", "border_color": "#059669", "image_url": ""},
                        {"id": "other", "title": "Diğer", "description": "Genel ilan ver", "module_key": "other", "border_color": "#7c3aed", "image_url": ""}
                    ]
                },
                "step2": {
                    "show_search": True,
                    "show_breadcrumb": True,
                    "mobile_stepper": True,
                    "continue_limit": 7,  # Change value to verify update
                    "require_leaf_before_continue": True
                },
                "step3": {
                    "block_order": ["core", "params", "address", "details", "media", "contact", "duration", "terms"],
                    "media": {"max_photos": 20, "max_videos": 1, "max_file_size_mb": 2, "accepted_types": ["image/png", "image/jpeg", "image/webp"]},
                    "contact": {"allow_phone_toggle": True, "allow_message_toggle": True},
                    "duration": {"show_discount_strike": True},
                    "terms": {"text": "Test terms text", "required": True}
                }
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/site/listing-design",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") == True, "Response should have 'ok': true"
        assert "config" in data, "Response should contain 'config'"
        
        # Verify the update was applied
        assert data["config"]["step2"]["continue_limit"] == 7, "continue_limit should be updated to 7"
        
        print(f"Admin listing design PUT: OK - updated successfully")
    
    def test_admin_endpoint_requires_auth(self):
        """GET /api/admin/site/listing-design without auth should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/admin/site/listing-design")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print(f"Admin listing design auth check: OK - returns {response.status_code} without token")


class TestPublicListingDesign:
    """Public listing design endpoint tests"""
    
    def test_get_public_listing_design(self):
        """GET /api/site/listing-design should be publicly accessible"""
        response = requests.get(f"{BASE_URL}/api/site/listing-design")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "config" in data, "Response should contain 'config'"
        
        config = data["config"]
        # Verify structure matches admin config
        assert "step1" in config, "Config should have 'step1'"
        assert "step2" in config, "Config should have 'step2'"
        assert "step3" in config, "Config should have 'step3'"
        
        print(f"Public listing design GET: OK - returns config with {len(config.get('step1', {}).get('cards', []))} cards")
    
    def test_public_endpoint_does_not_expose_setting_id(self):
        """Public endpoint should not expose internal setting_id"""
        response = requests.get(f"{BASE_URL}/api/site/listing-design")
        data = response.json()
        
        # setting_id should not be in public response (privacy/security)
        assert "setting_id" not in data, "Public response should not expose setting_id"
        print(f"Public listing design: OK - setting_id not exposed")


class TestListingDesignDataPersistence:
    """Test data persistence between GET and PUT operations"""
    
    def test_create_get_verify_flow(self, admin_token):
        """PUT config then GET to verify data persisted"""
        test_terms_text = "Test persistence: İlan kurallarını kabul ediyorum"
        
        # PUT new config
        update_payload = {
            "config": {
                "step1": {
                    "rows": 3,  # Changed from 2
                    "columns": 3,  # Changed from 4
                    "cards": [
                        {"id": "vehicle", "title": "Araç", "description": "Araç ilanı", "module_key": "vehicle", "border_color": "#2563eb", "image_url": ""}
                    ]
                },
                "step2": {
                    "show_search": False,  # Changed
                    "show_breadcrumb": True,
                    "mobile_stepper": True,
                    "continue_limit": 10,  # Changed
                    "require_leaf_before_continue": False  # Changed
                },
                "step3": {
                    "block_order": ["core", "params", "address", "details", "media", "contact", "duration", "terms"],
                    "media": {"max_photos": 15, "max_videos": 2, "max_file_size_mb": 3, "accepted_types": ["image/png"]},
                    "contact": {"allow_phone_toggle": False, "allow_message_toggle": True},
                    "duration": {"show_discount_strike": False},
                    "terms": {"text": test_terms_text, "required": True}
                }
            }
        }
        
        put_response = requests.put(
            f"{BASE_URL}/api/admin/site/listing-design",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_payload
        )
        assert put_response.status_code == 200, f"PUT failed: {put_response.text}"
        
        # GET to verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/admin/site/listing-design",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200, f"GET failed: {get_response.text}"
        
        saved_config = get_response.json()["config"]
        
        # Verify values were persisted
        assert saved_config["step1"]["rows"] == 3, "step1.rows should be 3"
        assert saved_config["step1"]["columns"] == 3, "step1.columns should be 3"
        assert saved_config["step2"]["continue_limit"] == 10, "step2.continue_limit should be 10"
        assert saved_config["step2"]["show_search"] == False, "step2.show_search should be False"
        
        print(f"Data persistence test: OK - all values persisted correctly")
        
        # Restore default config for other tests
        restore_payload = {
            "config": {
                "step1": {
                    "rows": 2,
                    "columns": 4,
                    "cards": [
                        {"id": "vehicle", "title": "Vasıta", "description": "Araç ilanı ver", "module_key": "vehicle", "border_color": "#2563eb", "image_url": ""},
                        {"id": "real_estate", "title": "Emlak", "description": "Emlak ilanı ver", "module_key": "real_estate", "border_color": "#059669", "image_url": ""},
                        {"id": "other", "title": "Diğer", "description": "Genel ilan ver", "module_key": "other", "border_color": "#7c3aed", "image_url": ""}
                    ]
                },
                "step2": {
                    "show_search": True,
                    "show_breadcrumb": True,
                    "mobile_stepper": True,
                    "continue_limit": 5,
                    "require_leaf_before_continue": True
                },
                "step3": {
                    "block_order": ["core", "params", "address", "details", "media", "contact", "duration", "terms"],
                    "media": {"max_photos": 20, "max_videos": 1, "max_file_size_mb": 2, "accepted_types": ["image/png", "image/jpeg", "image/webp"]},
                    "contact": {"allow_phone_toggle": True, "allow_message_toggle": True},
                    "duration": {"show_discount_strike": True},
                    "terms": {"text": "İlan verme kurallarını okudum, kabul ediyorum.", "required": True}
                }
            }
        }
        requests.put(
            f"{BASE_URL}/api/admin/site/listing-design",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=restore_payload
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
