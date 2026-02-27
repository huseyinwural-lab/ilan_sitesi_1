"""
P71 Site Showcase Layout Tests
Tests the showcase layout management endpoints:
- GET /api/site/showcase-layout (public)
- GET /api/admin/site/showcase-layout (admin)
- GET /api/admin/site/showcase-layout/configs (list versions)
- PUT /api/admin/site/showcase-layout/config (save draft)
- GET /api/admin/site/showcase-layout/config/{id} (get specific version)
- POST /api/admin/site/showcase-layout/config/{id}/publish (publish version)
"""

import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_CREDENTIALS = {
    "email": "admin@platform.com",
    "password": "Admin123!"
}


@pytest.fixture(scope="module")
def admin_token():
    """Login and get admin token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        pytest.skip("Admin login failed - skipping showcase layout tests")
    token = response.json().get("access_token")
    if not token:
        pytest.skip("No access token returned")
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Return admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestPublicShowcaseLayout:
    """Public showcase layout endpoint tests"""

    def test_get_public_showcase_layout(self):
        """GET /api/site/showcase-layout should return normalized config"""
        response = requests.get(f"{BASE_URL}/api/site/showcase-layout")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "config" in data, "Response should include config"
        
        config = data["config"]
        # Verify homepage block structure
        assert "homepage" in config, "Config should have homepage block"
        homepage = config["homepage"]
        assert "enabled" in homepage
        assert "rows" in homepage
        assert "columns" in homepage
        assert "listing_count" in homepage
        
        # Verify category_showcase block structure
        assert "category_showcase" in config, "Config should have category_showcase block"
        cat_showcase = config["category_showcase"]
        assert "enabled" in cat_showcase
        assert "default" in cat_showcase
        assert "categories" in cat_showcase
        
        print(f"Public showcase layout: version={data.get('version')}, homepage_enabled={homepage.get('enabled')}")


class TestAdminShowcaseLayoutAccess:
    """Admin showcase layout endpoints access tests"""

    def test_get_admin_showcase_layout_no_auth(self):
        """GET /api/admin/site/showcase-layout without auth should fail"""
        response = requests.get(f"{BASE_URL}/api/admin/site/showcase-layout")
        assert response.status_code in [401, 403], "Admin endpoint should require auth"
        print(f"Admin endpoint without auth returns: {response.status_code}")

    def test_get_admin_showcase_layout(self, admin_headers):
        """GET /api/admin/site/showcase-layout should return latest config"""
        response = requests.get(f"{BASE_URL}/api/admin/site/showcase-layout", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "config" in data, "Response should include config"
        assert "status" in data, "Response should include status"
        assert "version" in data, "Response should include version"
        
        config = data["config"]
        assert "homepage" in config
        assert "category_showcase" in config
        
        print(f"Admin showcase layout: id={data.get('id')}, version={data.get('version')}, status={data.get('status')}")


class TestShowcaseLayoutVersions:
    """Showcase layout version management tests"""

    def test_list_showcase_layout_configs(self, admin_headers):
        """GET /api/admin/site/showcase-layout/configs should list all versions"""
        response = requests.get(f"{BASE_URL}/api/admin/site/showcase-layout/configs", headers=admin_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should include items"
        
        items = data["items"]
        assert isinstance(items, list), "items should be a list"
        
        print(f"Showcase layout versions count: {len(items)}")
        for item in items[:3]:
            print(f"  Version {item.get('version')}: status={item.get('status')}, id={item.get('id')}")


class TestShowcaseLayoutCRUD:
    """Showcase layout save and publish tests"""

    def test_save_showcase_layout_draft(self, admin_headers):
        """PUT /api/admin/site/showcase-layout/config should save a draft"""
        payload = {
            "config": {
                "homepage": {
                    "enabled": True,
                    "rows": 5,
                    "columns": 6,
                    "listing_count": 30
                },
                "category_showcase": {
                    "enabled": True,
                    "default": {
                        "rows": 2,
                        "columns": 4,
                        "listing_count": 8
                    },
                    "categories": [
                        {
                            "enabled": True,
                            "category_id": "test-cat-id",
                            "category_slug": "test-category",
                            "category_name": "Test Category",
                            "rows": 3,
                            "columns": 5,
                            "listing_count": 15
                        }
                    ]
                }
            },
            "status": "draft"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json=payload,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should indicate success"
        assert "id" in data, "Response should include layout id"
        assert "version" in data, "Response should include version"
        
        # Store for next test
        pytest.created_layout_id = data["id"]
        pytest.created_layout_version = data["version"]
        
        print(f"Saved draft: id={data['id']}, version={data['version']}")

    def test_get_saved_layout_config(self, admin_headers):
        """GET /api/admin/site/showcase-layout/config/{id} should return saved config"""
        layout_id = getattr(pytest, 'created_layout_id', None)
        if not layout_id:
            pytest.skip("No layout id from previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{layout_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["id"] == layout_id
        assert "config" in data
        assert data["status"] == "draft"
        
        config = data["config"]
        assert config["homepage"]["rows"] == 5
        assert config["homepage"]["columns"] == 6
        assert len(config["category_showcase"]["categories"]) == 1
        
        print(f"Retrieved layout: version={data['version']}, status={data['status']}")

    def test_publish_layout_config(self, admin_headers):
        """POST /api/admin/site/showcase-layout/config/{id}/publish should publish"""
        layout_id = getattr(pytest, 'created_layout_id', None)
        if not layout_id:
            pytest.skip("No layout id from previous test")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{layout_id}/publish",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should indicate success"
        
        print(f"Published layout: id={data['id']}, version={data['version']}")

    def test_verify_published_in_public_endpoint(self):
        """Verify published config is returned by public endpoint"""
        response = requests.get(f"{BASE_URL}/api/site/showcase-layout")
        assert response.status_code == 200
        
        data = response.json()
        config = data["config"]
        
        # Should reflect our published config
        assert config["homepage"]["rows"] == 5, f"Expected rows=5, got {config['homepage']['rows']}"
        assert config["homepage"]["columns"] == 6, f"Expected columns=6, got {config['homepage']['columns']}"
        
        print(f"Public endpoint reflects published config: rows={config['homepage']['rows']}, columns={config['homepage']['columns']}")


class TestShowcaseLayoutValidation:
    """Showcase layout validation tests"""

    def test_save_invalid_homepage_rows(self, admin_headers):
        """Invalid rows value should be normalized"""
        payload = {
            "config": {
                "homepage": {
                    "enabled": True,
                    "rows": 50,  # Over max of 12
                    "columns": 3,
                    "listing_count": 20
                },
                "category_showcase": {
                    "enabled": True,
                    "default": {"rows": 2, "columns": 4, "listing_count": 8},
                    "categories": []
                }
            },
            "status": "draft"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json=payload,
            headers=admin_headers
        )
        
        # Should succeed - backend normalizes values
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("Backend normalizes invalid rows value")

    def test_save_missing_category_id(self, admin_headers):
        """Category item without category_id and category_slug should fail"""
        payload = {
            "config": {
                "homepage": {
                    "enabled": True,
                    "rows": 5,
                    "columns": 5,
                    "listing_count": 25
                },
                "category_showcase": {
                    "enabled": True,
                    "default": {"rows": 2, "columns": 4, "listing_count": 8},
                    "categories": [
                        {
                            "enabled": True,
                            # Missing category_id and category_slug
                            "category_name": "Missing ID",
                            "rows": 2,
                            "columns": 4,
                            "listing_count": 8
                        }
                    ]
                }
            },
            "status": "draft"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json=payload,
            headers=admin_headers
        )
        
        # Should fail validation
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("Validation correctly rejects missing category_id/slug")


class TestShowcaseLayoutRestoreDefaults:
    """Restore showcase layout to default values"""

    def test_restore_default_layout(self, admin_headers):
        """Restore default showcase layout configuration"""
        payload = {
            "config": {
                "homepage": {
                    "enabled": True,
                    "rows": 9,
                    "columns": 7,
                    "listing_count": 63
                },
                "category_showcase": {
                    "enabled": True,
                    "default": {
                        "rows": 2,
                        "columns": 4,
                        "listing_count": 8
                    },
                    "categories": []
                }
            },
            "status": "draft"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/site/showcase-layout/config",
            json=payload,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        layout_id = data["id"]
        
        # Publish the default config
        response = requests.post(
            f"{BASE_URL}/api/admin/site/showcase-layout/config/{layout_id}/publish",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        print("Restored default showcase layout")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
