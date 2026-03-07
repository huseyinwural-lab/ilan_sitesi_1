"""
Iteration 169: Faz B + Faz C + RBAC Testing

This test suite covers:
- Faz B: /kategori/:slug flow with content_builder_only policy
- Faz C: SearchPage resolve with source_policy=content_builder_only and allowDraftPreview=false
- Faz C: DetailPage deterministic error behavior (listing-detail-layout-empty-state)
- Backend policy enforcement: invalid_source_policy => 400, content_builder_only + draft => 400
- Content-list C criteria: page loading + error quick actions
- RBAC: dealer/user cannot access admin content endpoints (403)
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestAuthHelpers:
    """Helper methods for authentication"""
    
    @staticmethod
    def get_admin_token():
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=30,
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("access_token")
    
    @staticmethod
    def get_dealer_token():
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
            timeout=30,
        )
        assert response.status_code == 200, f"Dealer login failed: {response.text}"
        return response.json().get("access_token")
    
    @staticmethod
    def get_user_token():
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "user@platform.com", "password": "User123!"},
            timeout=30,
        )
        assert response.status_code == 200, f"User login failed: {response.text}"
        return response.json().get("access_token")


# ============================================================
# Faz B: Policy enforcement on resolve endpoint
# ============================================================

class TestFazBPolicyEnforcement:
    """Tests for Faz B - source_policy enforcement on resolve API"""
    
    def test_resolve_rejects_invalid_source_policy(self):
        """Backend must return 400 for invalid source_policy values"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "source_policy": "invalid_policy",
            },
            timeout=30,
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert response.json().get("detail") == "invalid_source_policy"
    
    def test_resolve_rejects_empty_unknown_policy(self):
        """Backend allows empty policy but rejects unknown non-empty policies"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "source_policy": "some_random_policy",
            },
            timeout=30,
        )
        assert response.status_code == 400
        assert response.json().get("detail") == "invalid_source_policy"
    
    def test_content_builder_only_rejects_draft_preview_for_home(self):
        """content_builder_only + draft preview must return 400 for home page"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "source_policy": "content_builder_only",
                "layout_preview": "draft",
            },
            timeout=30,
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert response.json().get("detail") == "content_builder_only_requires_published_preview"
    
    def test_content_builder_only_allows_published_or_no_preview(self):
        """content_builder_only should work without layout_preview param"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "source_policy": "content_builder_only",
            },
            timeout=30,
        )
        # May return 200 with layout or 404 if no published layout exists
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    
    def test_resolve_accepts_empty_source_policy(self):
        """Empty source_policy should be accepted (default behavior)"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "source_policy": "",
            },
            timeout=30,
        )
        # Should not return 400 for empty policy
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"


# ============================================================
# Faz C: Search page resolve behavior
# ============================================================

class TestFazCSearchPageBehavior:
    """Tests for Faz C - SearchPage deterministic empty state"""
    
    def test_search_ln_page_type_resolve(self):
        """search_ln page type should work with content_builder_only
        Returns 200 if published layout exists, 404/409 if no published revision
        409 = default_layout_has_no_published_revision (deterministic error, not silent fallback)
        """
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "search_ln",
                "source_policy": "content_builder_only",
            },
            timeout=30,
        )
        # 200 = published layout found
        # 404 = no layout page exists
        # 409 = layout page exists but no published revision (deterministic error)
        assert response.status_code in [200, 404, 409]
        if response.status_code == 409:
            assert "no_published_revision" in response.json().get("detail", "") or "default_layout_has_no_published_revision" in response.json().get("detail", "")
    
    def test_category_l0_l1_page_type_resolve(self):
        """category_l0_l1 page type should work with content_builder_only"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "category_l0_l1",
                "source_policy": "content_builder_only",
            },
            timeout=30,
        )
        # 409 = deterministic error when no published revision
        assert response.status_code in [200, 404, 409]
    
    def test_urgent_listings_page_type_resolve(self):
        """urgent_listings page type should work with content_builder_only"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "urgent_listings",
                "source_policy": "content_builder_only",
            },
            timeout=30,
        )
        # 409 = deterministic error when no published revision
        assert response.status_code in [200, 404, 409]


# ============================================================
# Faz C: DetailPage deterministic error behavior
# ============================================================

class TestFazCDetailPageBehavior:
    """Tests for Faz C - DetailPage empty state"""
    
    def test_listing_detail_page_type_resolve(self):
        """listing_detail page type should work with content_builder_only
        409 = deterministic error for "no published revision" (triggers empty state on frontend)
        """
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "vehicle",
                "page_type": "listing_detail",
                "source_policy": "content_builder_only",
            },
            timeout=30,
        )
        # 200 = published layout found
        # 404 = no layout page exists
        # 409 = layout page exists but no published revision (triggers empty state)
        assert response.status_code in [200, 404, 409]


# ============================================================
# RBAC: dealer/user cannot access admin endpoints
# ============================================================

class TestRBACContentEndpoints:
    """RBAC tests - dealer/user should get 403 on admin content endpoints"""
    
    def test_dealer_cannot_access_admin_layouts_list(self):
        """Dealer role should not access GET /api/admin/layouts"""
        token = TestAuthHelpers.get_dealer_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"
    
    def test_user_cannot_access_admin_layouts_list(self):
        """User role should not access GET /api/admin/layouts"""
        token = TestAuthHelpers.get_user_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert response.status_code == 403, f"Expected 403 for user, got {response.status_code}"
    
    def test_admin_can_access_layouts_list(self):
        """Admin role should access GET /api/admin/layouts"""
        token = TestAuthHelpers.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "limit": 10},
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200 for admin, got {response.status_code}"
    
    def test_dealer_cannot_publish_layout(self):
        """Dealer should not be able to create a layout page (POST /admin/site/content-layout/pages)"""
        token = TestAuthHelpers.get_dealer_token()
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "page_type": "home",
                "country": "DE",
                "module": "global",
            },
            timeout=30,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"
    
    def test_user_cannot_create_layout_page(self):
        """User should not be able to create layout page"""
        token = TestAuthHelpers.get_user_token()
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "page_type": "home",
                "country": "DE",
                "module": "global",
            },
            timeout=30,
        )
        assert response.status_code == 403, f"Expected 403 for user, got {response.status_code}"
    
    def test_dealer_cannot_access_template_pack_install(self):
        """Dealer should not access POST /api/admin/site/content-layout/preset/install-standard-pack"""
        token = TestAuthHelpers.get_dealer_token()
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "countries": ["DE"],
                "module": "global",
            },
            timeout=30,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"
    
    def test_user_cannot_access_template_pack_verify(self):
        """User should not access GET /api/admin/site/content-layout/preset/verify-standard-pack"""
        token = TestAuthHelpers.get_user_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers={"Authorization": f"Bearer {token}"},
            params={"countries": "DE", "module": "global"},
            timeout=30,
        )
        assert response.status_code == 403, f"Expected 403 for user, got {response.status_code}"


# ============================================================
# Content List Admin Access (positive tests)
# ============================================================

class TestContentListAdminAccess:
    """Tests for admin Content List access"""
    
    def test_admin_layouts_list_returns_items(self):
        """GET /api/admin/layouts should return items array"""
        token = TestAuthHelpers.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "limit": 50},
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_admin_layouts_list_filters_by_status(self):
        """GET /api/admin/layouts should accept status filter"""
        token = TestAuthHelpers.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {token}"},
            params={"statuses": "draft,published", "page": 1, "limit": 50},
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_admin_layouts_include_deleted(self):
        """GET /api/admin/layouts with include_deleted should work"""
        token = TestAuthHelpers.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {token}"},
            params={"include_deleted": "true", "page": 1, "limit": 50},
            timeout=30,
        )
        assert response.status_code == 200


# ============================================================
# Regression: Category delete/undo flows
# ============================================================

class TestCategoryRegressions:
    """Regression tests for category delete/undo and list/search UX"""
    
    def test_categories_list_endpoint_works(self):
        """GET /api/admin/categories should return paginated list"""
        token = TestAuthHelpers.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "limit": 20, "country": "DE"},
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
    
    def test_categories_tree_endpoint_works(self):
        """GET /api/categories/tree should work"""
        response = requests.get(
            f"{BASE_URL}/api/categories/tree",
            params={"country": "DE", "module": "vehicle"},
            timeout=30,
        )
        assert response.status_code == 200
    
    def test_delete_operations_history_accessible(self):
        """GET /api/admin/categories/delete-operations should work for admin"""
        token = TestAuthHelpers.get_admin_token()
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/delete-operations",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "limit": 20},
            timeout=30,
        )
        # May return 200 with items or 404 if no operations exist
        assert response.status_code in [200, 404]


# ============================================================
# Frontend code gate verification
# ============================================================

class TestFrontendCodeGates:
    """Verify frontend code has the required policy gates"""
    
    def test_home_page_source_policy_gate_present(self):
        """HomePageRefreshed.js must have content_builder_only policy"""
        from pathlib import Path
        content = Path("/app/frontend/src/pages/public/HomePageRefreshed.js").read_text()
        assert "sourcePolicy: 'content_builder_only'" in content
        assert "allowDraftPreview: false" in content
    
    def test_search_page_source_policy_gate_present(self):
        """SearchPage.js must have content_builder_only policy"""
        from pathlib import Path
        content = Path("/app/frontend/src/pages/public/SearchPage.js").read_text()
        assert "sourcePolicy: 'content_builder_only'" in content
        assert "allowDraftPreview: false" in content
    
    def test_detail_page_source_policy_gate_present(self):
        """DetailPage.js must have content_builder_only policy and empty state"""
        from pathlib import Path
        content = Path("/app/frontend/src/pages/public/DetailPage.js").read_text()
        assert "sourcePolicy: 'content_builder_only'" in content
        assert "allowDraftPreview: false" in content
        assert "listing-detail-layout-empty-state" in content
    
    def test_resolve_api_enforces_source_policy_rules(self):
        """Backend layout_builder_routes.py must enforce policy rules"""
        from pathlib import Path
        content = Path("/app/backend/app/routers/layout_builder_routes.py").read_text()
        assert "invalid_source_policy" in content
        assert "content_builder_only_requires_published_preview" in content


# ============================================================
# Public resolve endpoint (no auth required)
# ============================================================

class TestPublicResolveEndpoint:
    """Tests for public resolve endpoint behavior"""
    
    def test_resolve_endpoint_is_public(self):
        """Resolve endpoint should not require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
            },
            timeout=30,
        )
        # Should return 200 or 404, not 401/403
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
    
    def test_resolve_returns_revision_payload(self):
        """If layout exists, resolve should return revision with payload_json"""
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "source_policy": "content_builder_only",
            },
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            assert "revision" in data
            assert "payload_json" in data.get("revision", {})
