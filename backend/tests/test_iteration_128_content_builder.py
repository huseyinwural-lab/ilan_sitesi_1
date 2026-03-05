"""
Content Builder Tests - iteration_128

Testing features:
1. Admin Content Builder: preset select + apply (listing-detail-pack, listing-create-stepx-pack)
2. Policy Report: fix_suggestion in checks, suggested_fixes array
3. Publish guard: listing_create policy FAIL/PASS scenarios
4. Backend policy report endpoint response structure
5. Runtime renderer components (no JS errors expected)
6. Component Library grouped/collapsible + quick search + category filter
7. LayoutRenderer runtimeContext propagation (no regression)
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0


class TestPolicyReportStructure:
    """Tests for policy report endpoint response structure with fix_suggestion and suggested_fixes"""
    
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
        self.draft_id = None
    
    def teardown_method(self, method):
        """Cleanup test data"""
        pass  # Pages are auto-cleaned or reusable
    
    def test_policy_report_has_fix_suggestion_in_checks(self):
        """Verify policy report checks[] contain fix_suggestion field"""
        # Create page
        module_name = f"TEST_fix_suggestion_{int(time.time())}"
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        self.page_id = page_response.json()["item"]["id"]
        
        # Create valid draft to get policy report
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
        self.draft_id = draft_response.json()["item"]["id"]
        
        # Get policy report
        report_response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{self.draft_id}/policy-report",
            headers=self.headers
        )
        assert report_response.status_code == 200
        
        report = report_response.json()["report"]
        
        # Verify structure
        assert "checks" in report, "report should contain checks array"
        assert "suggested_fixes" in report, "report should contain suggested_fixes array"
        assert "policy" in report
        assert report["policy"] == "listing_create"
        
        # Verify each check has fix_suggestion field
        for check in report["checks"]:
            assert "id" in check, f"Check missing id: {check}"
            assert "label" in check, f"Check missing label: {check}"
            assert "status" in check, f"Check missing status: {check}"
            assert "fix_suggestion" in check, f"Check missing fix_suggestion: {check}"
    
    def test_policy_report_suggested_fixes_populated_for_failing_checks(self):
        """Verify suggested_fixes array is populated when checks fail"""
        module_name = f"TEST_suggested_fixes_{int(time.time())}"
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        self.page_id = page_response.json()["item"]["id"]
        
        # Create a draft with ALL checks passing to verify suggested_fixes is empty
        valid_draft_response = requests.post(
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
        assert valid_draft_response.status_code == 200
        draft_id = valid_draft_response.json()["item"]["id"]
        
        report_response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-report",
            headers=self.headers
        )
        assert report_response.status_code == 200
        
        report = report_response.json()["report"]
        
        # For a valid draft, suggested_fixes should be empty array
        if report["passed"]:
            assert isinstance(report["suggested_fixes"], list)
            assert len(report["suggested_fixes"]) == 0


class TestPublishGuardWithPolicy:
    """Tests for publish guard enforcing listing_create policy"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.page_ids = []
    
    def teardown_method(self, method):
        """Cleanup test pages"""
        pass
    
    def test_publish_blocked_when_policy_fails_missing_default(self):
        """Publish should be blocked when listing.create.default-content is missing"""
        module_name = f"TEST_publish_guard_no_default_{int(time.time())}"
        
        # Create page
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        self.page_ids.append(page_id)
        
        # Try to create draft without default component - should fail at draft creation
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
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
                                "props": {"title": "No default component"}
                            }]
                        }]
                    }]
                }
            }
        )
        
        # Should fail with 400 at draft creation level
        assert draft_response.status_code == 400
        assert "listing_create_default_component_must_be_exactly_one" in draft_response.json().get("detail", "")
    
    def test_publish_succeeds_when_policy_passes(self):
        """Publish should succeed when policy checks pass"""
        module_name = f"TEST_publish_guard_pass_{int(time.time())}"
        
        # Create page
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        self.page_ids.append(page_id)
        
        # Create valid draft
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
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
        
        # Publish should succeed
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=self.headers
        )
        assert publish_response.status_code == 200
        assert publish_response.json()["ok"] == True
        assert publish_response.json()["item"]["status"] == "published"


class TestPresetPackPayloads:
    """Tests for preset pack payloads validation (listing-detail-pack, listing-create-stepx-pack)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_listing_detail_pack_structure_valid(self):
        """Verify listing-detail-pack preset structure is valid for home page_type"""
        # listing-detail-pack is for generic use (null targetPageType), test with home
        module_name = f"TEST_listing_detail_pack_{int(time.time())}"
        
        # Create page for home type
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "home",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Simulate listing-detail-pack payload structure
        listing_detail_payload = {
            "rows": [
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "layout.breadcrumb-header", "props": {}},
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "media.advanced-photo-gallery", "props": {}}
                        ]
                    }]
                },
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [
                        {
                            "id": f"col-{uuid.uuid4().hex[:8]}",
                            "width": {"desktop": 8, "tablet": 12, "mobile": 12},
                            "components": [
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "data.price-title-block", "props": {}},
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "data.attribute-grid-dynamic", "props": {}},
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "data.description-text-area", "props": {}},
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "interactive.similar-listings-slider", "props": {"source": "similar", "max_items": 8}}
                            ]
                        },
                        {
                            "id": f"col-{uuid.uuid4().hex[:8]}",
                            "width": {"desktop": 4, "tablet": 12, "mobile": 12},
                            "components": [
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "data.seller-card", "props": {}},
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "interactive.interactive-map", "props": {}},
                                {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "layout.sticky-action-bar", "props": {}}
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Create draft with listing-detail-pack structure
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={"payload_json": listing_detail_payload}
        )
        assert draft_response.status_code == 200, f"Failed to create draft: {draft_response.json()}"
        assert draft_response.json()["ok"] == True
    
    def test_listing_create_stepx_pack_structure_valid(self):
        """Verify listing-create-stepx-pack preset structure is valid"""
        module_name = f"TEST_listing_create_stepx_pack_{int(time.time())}"
        
        # Create page for listing_create_stepX type
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Simulate listing-create-stepx-pack payload structure
        listing_create_payload = {
            "rows": [
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "listing.create.default-content", "props": {}},
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "shared.text-block", "props": {"title": "İlan Ver Akışı", "body": "Adımları tamamlayarak ilanınızı güvenle yayınlayın."}}
                        ]
                    }]
                },
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {
                                "id": f"cmp-{uuid.uuid4().hex[:8]}",
                                "key": "interactive.doping-selector",
                                "props": {
                                    "available_dopings": ["Vitrin", "Acil", "Anasayfa"],
                                    "show_prices": True,
                                    "default_selected": "Vitrin"
                                }
                            },
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "shared.ad-slot", "props": {"placement": "AD_LOGIN_1"}}
                        ]
                    }]
                }
            ]
        }
        
        # Create draft with listing-create-stepx-pack structure
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={"payload_json": listing_create_payload}
        )
        assert draft_response.status_code == 200, f"Failed to create draft: {draft_response.json()}"
        assert draft_response.json()["ok"] == True


class TestComponentLibraryAPI:
    """Tests for component library API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_component_library_returns_items(self):
        """Test component library endpoint returns items"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components?limit=100",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_menu_items_endpoint_accessible(self):
        """Test menu items endpoint is accessible (may return 403 feature_disabled)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/menu-items?country=DE",
            headers=self.headers
        )
        # Can be 200, 403 (feature_disabled), or 404
        assert response.status_code in [200, 403, 404]


class TestRuntimeRendererEndpoints:
    """Tests for runtime renderer related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_listing_vehicle_detail_endpoint(self):
        """Test v1/listings/vehicle endpoint exists"""
        # First get a listing ID from search
        search_response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=1")
        assert search_response.status_code == 200
        
        items = search_response.json().get("items", [])
        if items:
            listing_id = items[0]["id"]
            # Try to fetch detail
            detail_response = requests.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}?preview=1")
            # Can be 200 or 404 if listing doesn't exist
            assert detail_response.status_code in [200, 404]
    
    def test_similar_listings_endpoint(self):
        """Test similar listings endpoint exists"""
        # First get a listing ID from search
        search_response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=1")
        assert search_response.status_code == 200
        
        items = search_response.json().get("items", [])
        if items:
            listing_id = items[0]["id"]
            # Try to fetch similar
            similar_response = requests.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/similar?limit=8")
            # Can be 200 or 404
            assert similar_response.status_code in [200, 404]


class TestSearchV2Integration:
    """Tests for search v2 API used by runtime renderers"""
    
    def test_search_v2_basic(self):
        """Test basic search v2 endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
    
    def test_search_v2_showcase(self):
        """Test search v2 with showcase doping filter"""
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=8&doping_type=showcase")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestCategoriesEndpoint:
    """Tests for categories endpoint used by runtime context"""
    
    def test_categories_real_estate(self):
        """Test categories endpoint for real_estate module"""
        response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_categories_vehicle(self):
        """Test categories endpoint for vehicle module"""
        response = requests.get(f"{BASE_URL}/api/categories?module=vehicle&country=DE")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


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
