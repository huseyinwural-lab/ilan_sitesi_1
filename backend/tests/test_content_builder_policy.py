"""
Content Builder Policy Tests - iteration_127

Testing features:
1. Component Library API
2. listing_create policy enforcement
3. Policy report endpoint
4. Publish guard for listing_create pages
5. Doping selector validation
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Admin authentication tests"""
    
    def test_admin_login(self):
        """Test admin login to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        return data["access_token"]


class TestComponentLibrary:
    """Component Library API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_components(self):
        """Test listing component definitions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components?limit=100",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_layout_pages(self):
        """Test listing layout pages"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages?limit=50",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestListingCreatePolicy:
    """listing_create policy enforcement tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create test page"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.page_id = None
    
    def teardown_method(self, method):
        """Cleanup test page if created"""
        if self.page_id:
            requests.delete(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}",
                headers=self.headers
            )
    
    def test_create_draft_without_default_component_fails(self):
        """Draft without listing.create.default-content should fail"""
        # Create test page
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": f"TEST_policy_no_default_{int(time.time())}"
            }
        )
        assert response.status_code in [200, 201]
        self.page_id = response.json()["item"]["id"]
        
        # Try to create draft without default component
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [{
                                "id": "cmp-text",
                                "key": "shared.text-block",
                                "props": {"title": "Test"}
                            }]
                        }]
                    }]
                }
            }
        )
        # Should fail with 400
        assert draft_response.status_code == 400
        assert "listing_create_default_component_must_be_exactly_one" in draft_response.json().get("detail", "")
    
    def test_create_draft_with_invalid_doping_option_fails(self):
        """Draft with invalid doping option should fail"""
        # Create test page
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": f"TEST_policy_invalid_doping_{int(time.time())}"
            }
        )
        assert response.status_code in [200, 201]
        self.page_id = response.json()["item"]["id"]
        
        # Try to create draft with invalid doping option
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [
                                {
                                    "id": "cmp-default",
                                    "key": "listing.create.default-content",
                                    "props": {}
                                },
                                {
                                    "id": "cmp-doping",
                                    "key": "interactive.doping-selector",
                                    "props": {
                                        "available_dopings": ["Vitrin", "INVALID_DOPING"],
                                        "show_prices": True
                                    }
                                }
                            ]
                        }]
                    }]
                }
            }
        )
        # Should fail with 400
        assert draft_response.status_code == 400
        assert "listing_create_doping_option_not_allowed" in draft_response.json().get("detail", "")
    
    def test_create_valid_draft_succeeds(self):
        """Valid draft with default component should succeed"""
        # Create test page
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": f"TEST_policy_valid_{int(time.time())}"
            }
        )
        assert response.status_code in [200, 201]
        self.page_id = response.json()["item"]["id"]
        
        # Create valid draft
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [{
                                "id": "cmp-default",
                                "key": "listing.create.default-content",
                                "props": {}
                            }]
                        }]
                    }]
                }
            }
        )
        assert draft_response.status_code == 200
        assert draft_response.json()["ok"] == True
        return draft_response.json()["item"]["id"]


class TestPolicyReport:
    """Policy report endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.page_id = None
    
    def teardown_method(self, method):
        """Cleanup test page"""
        if self.page_id:
            requests.delete(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}",
                headers=self.headers
            )
    
    def test_policy_report_for_valid_draft(self):
        """Policy report for valid draft should return PASS"""
        # Create page and draft
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": f"TEST_policy_report_{int(time.time())}"
            }
        )
        self.page_id = page_response.json()["item"]["id"]
        
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [
                                {
                                    "id": "cmp-default",
                                    "key": "listing.create.default-content",
                                    "props": {}
                                },
                                {
                                    "id": "cmp-doping",
                                    "key": "interactive.doping-selector",
                                    "props": {
                                        "available_dopings": ["Vitrin", "Acil", "Anasayfa"],
                                        "show_prices": True
                                    }
                                }
                            ]
                        }]
                    }]
                }
            }
        )
        assert draft_response.status_code == 200
        draft_id = draft_response.json()["item"]["id"]
        
        # Get policy report
        report_response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-report",
            headers=self.headers
        )
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["ok"] == True
        assert report["report"]["passed"] == True
        assert report["report"]["policy"] == "listing_create"
        
        # Verify all checks passed
        for check in report["report"]["checks"]:
            assert check["status"] == "pass", f"Check {check['name']} failed: {check.get('value')}"


class TestPublishGuard:
    """Publish guard tests for listing_create"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.page_id = None
    
    def teardown_method(self, method):
        """Cleanup test page"""
        if self.page_id:
            requests.delete(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}",
                headers=self.headers
            )
    
    def test_publish_valid_draft_succeeds(self):
        """Publishing valid draft with PASS policy should succeed"""
        # Create page and valid draft
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": f"TEST_publish_valid_{int(time.time())}"
            }
        )
        self.page_id = page_response.json()["item"]["id"]
        
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{self.page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [{
                                "id": "cmp-default",
                                "key": "listing.create.default-content",
                                "props": {}
                            }]
                        }]
                    }]
                }
            }
        )
        assert draft_response.status_code == 200
        draft_id = draft_response.json()["item"]["id"]
        
        # Publish the draft
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=self.headers
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["ok"] == True
        assert publish_response.json()["item"]["status"] == "published"


class TestHealthCheck:
    """Health check tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
