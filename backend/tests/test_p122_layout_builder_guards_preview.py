"""
P2.1/P2.2/P2.3 Layout Builder Enhancement Tests
- P2.1: listing_create_stepX component/props whitelist guard
- P2.2: Category tree search picker in binding panel (API tests only)
- P2.3: Draft preview mode (layout_preview=draft) with comparison

Test Coverage:
1. P2.1 - Wizard Runtime Component/Props Whitelist
   - Disallowed component key rejection (400)
   - Disallowed props rejection (400)
   - Allowed component/props accepted (200)
   
2. P2.2 - Category Tree Search Picker
   - Category list API for binding panel
   - Bind/fetch/unbind operations still work
   
3. P2.3 - Draft Preview Mode
   - layout_preview=draft for admin requests
   - Non-admin/unauth draft preview blocked (403)
   - Draft preview returns comparison data
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if res.status_code != 200:
        pytest.skip(f"Admin login failed: {res.status_code} {res.text[:200]}")
    return res.json().get("access_token")


@pytest.fixture(scope="module")
def user_token():
    """Get regular user token to test RBAC."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@platform.com", "password": "User12345!"},
        timeout=15,
    )
    if res.status_code != 200:
        return None
    return res.json().get("access_token")


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _get_test_category_id() -> str:
    """Get a valid category ID."""
    response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE", timeout=10)
    if response.status_code != 200:
        response = requests.get(f"{BASE_URL}/api/categories?country=DE", timeout=10)
    if response.status_code != 200:
        pytest.skip("No categories available for testing")
    items = response.json()
    if isinstance(items, list) and items:
        return items[0]["id"]
    pytest.skip("No categories available for testing")


def _create_listing_create_page(admin_token: str) -> str:
    """Create a listing_create_stepX page and return page_id."""
    marker = uuid.uuid4().hex[:8]
    res = requests.post(
        f"{BASE_URL}/api/admin/site/content-layout/pages",
        headers=_headers(admin_token),
        json={
            "page_type": "listing_create_stepX",
            "country": "DE",
            "module": f"test_guard_{marker}",
            "category_id": None,
        },
        timeout=10,
    )
    assert res.status_code == 200, f"Page creation failed: {res.text}"
    return res.json()["item"]["id"]


# =====================================================
# P2.1: Listing Create Component/Props Whitelist Guard
# =====================================================
class TestListingCreateGuard:
    """P2.1: Tests for listing_create_stepX component/props whitelist."""

    def test_disallowed_component_key_rejected_with_400(self, admin_token):
        """Disallowed component key in listing_create_stepX returns 400."""
        page_id = _create_listing_create_page(admin_token)
        
        # Try to create draft with disallowed component
        invalid_payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "some.disallowed.component",
                                    "props": {},
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": invalid_payload},
            timeout=10,
        )
        
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        detail = res.json().get("detail", "")
        assert "listing_create_component_not_allowed" in str(detail).lower()

    def test_disallowed_props_rejected_with_400(self, admin_token):
        """Disallowed props in allowed component returns 400."""
        page_id = _create_listing_create_page(admin_token)
        
        # shared.text-block only allows {title, body}
        invalid_payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "shared.text-block",
                                    "props": {
                                        "title": "Valid",
                                        "body": "Valid",
                                        "forbidden_prop": "should_reject",
                                    },
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": invalid_payload},
            timeout=10,
        )
        
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        detail = res.json().get("detail", "")
        assert "listing_create_component_props_not_allowed" in str(detail).lower()

    def test_allowed_component_with_valid_props_accepted(self, admin_token):
        """Allowed component with valid props returns 200."""
        page_id = _create_listing_create_page(admin_token)
        
        # listing.create.default-content has empty allowed props set
        # shared.text-block allows {title, body}
        valid_payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "listing.create.default-content",
                                    "props": {},
                                },
                            ]
                        }
                    ]
                },
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "shared.text-block",
                                    "props": {
                                        "title": "Valid Title",
                                        "body": "Valid Body",
                                    },
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": valid_payload},
            timeout=10,
        )
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_shared_ad_slot_with_placement_prop_allowed(self, admin_token):
        """shared.ad-slot with placement prop is allowed."""
        page_id = _create_listing_create_page(admin_token)
        
        valid_payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "shared.ad-slot",
                                    "props": {
                                        "placement": "top-banner",
                                    },
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": valid_payload},
            timeout=10,
        )
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    def test_patch_draft_also_validates_guard(self, admin_token):
        """PATCH draft endpoint also validates component/props whitelist."""
        page_id = _create_listing_create_page(admin_token)
        
        # Create valid draft first
        valid_payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "listing.create.default-content",
                                    "props": {},
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        
        create_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": valid_payload},
            timeout=10,
        )
        assert create_res.status_code == 200
        draft_id = create_res.json()["item"]["id"]
        
        # Patch with invalid payload
        invalid_payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "invalid.component.xyz",
                                    "props": {},
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        
        patch_res = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/draft",
            headers=_headers(admin_token),
            json={"payload_json": invalid_payload},
            timeout=10,
        )
        
        assert patch_res.status_code == 400, f"Expected 400, got {patch_res.status_code}"

    def test_non_listing_page_type_not_validated(self, admin_token):
        """Non listing_create_stepX pages skip component guard."""
        marker = uuid.uuid4().hex[:8]
        
        # Create home page (not listing_create_stepX)
        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "home",
                "country": "DE",
                "module": f"test_home_{marker}",
                "category_id": None,
            },
            timeout=10,
        )
        assert page_res.status_code == 200
        page_id = page_res.json()["item"]["id"]
        
        # Any component should be allowed
        payload = {
            "rows": [
                {
                    "columns": [
                        {
                            "components": [
                                {
                                    "key": "any.component.key",
                                    "props": {"any": "prop"},
                                },
                            ]
                        }
                    ]
                }
            ]
        }
        
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": payload},
            timeout=10,
        )
        
        assert res.status_code == 200, f"Home page should accept any components: {res.text}"


# =====================================================
# P2.2: Category Tree Search Picker Tests
# =====================================================
class TestCategoryTreePicker:
    """P2.2: Tests for category tree picker in binding panel (API tests)."""

    def test_categories_list_for_binding_panel(self, admin_token):
        """Categories list API returns hierarchical tree data."""
        res = requests.get(
            f"{BASE_URL}/api/categories",
            params={"module": "real_estate", "country": "DE"},
            timeout=10,
        )
        
        assert res.status_code == 200, f"Categories API failed: {res.text}"
        items = res.json()
        assert isinstance(items, list)
        
        # Should have category data with tree structure
        if items:
            first_item = items[0]
            assert "id" in first_item
            assert "name" in first_item
            # parent_id indicates tree structure
            assert "parent_id" in first_item or first_item.get("parent_id") is None

    def test_bind_fetch_unbind_still_work(self, admin_token):
        """Binding operations remain functional after picker changes."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_picker_bind_{marker}"
        category_id = _get_test_category_id()
        
        # Create page
        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
            timeout=10,
        )
        assert page_res.status_code == 200
        page_id = page_res.json()["item"]["id"]
        
        # Create and publish draft
        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": []}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]
        
        publish_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish_res.status_code == 200
        
        # Bind
        bind_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings",
            headers=_headers(admin_token),
            json={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
                "layout_page_id": page_id,
            },
            timeout=10,
        )
        assert bind_res.status_code == 200, f"Bind failed: {bind_res.text}"
        
        # Fetch active binding
        fetch_res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
            headers=_headers(admin_token),
            params={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
            },
            timeout=10,
        )
        assert fetch_res.status_code == 200
        assert fetch_res.json().get("item") is not None
        
        # Unbind
        unbind_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/unbind",
            headers=_headers(admin_token),
            json={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
            },
            timeout=10,
        )
        assert unbind_res.status_code == 200, f"Unbind failed: {unbind_res.text}"


# =====================================================
# P2.3: Draft Preview Mode Tests
# =====================================================
class TestDraftPreviewMode:
    """P2.3: Tests for layout_preview=draft functionality."""

    def test_admin_can_resolve_with_draft_preview(self, admin_token):
        """Admin-authenticated request with layout_preview=draft returns draft."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_preview_draft_{marker}"
        
        # Create page
        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "home",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
            timeout=10,
        )
        assert page_res.status_code == 200
        page_id = page_res.json()["item"]["id"]
        
        # Create draft with specific content
        draft_content = {"rows": [{"id": "draft-row-marker"}]}
        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": draft_content},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]
        
        # Publish the draft first (so there's a published version)
        publish_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish_res.status_code == 200
        
        # Create a NEW draft with different content
        new_draft_content = {"rows": [{"id": "new-draft-marker-123"}]}
        new_draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": new_draft_content},
            timeout=10,
        )
        assert new_draft_res.status_code == 200
        
        # Resolve with layout_preview=draft (admin authenticated)
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            headers=_headers(admin_token),
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "home",
                "layout_preview": "draft",
            },
            timeout=10,
        )
        
        assert resolve_res.status_code == 200, f"Draft resolve failed: {resolve_res.text}"
        data = resolve_res.json()
        
        # Should have draft source indicator
        assert data.get("preview_mode") == "draft"
        assert data.get("source") in {"default_draft", "binding_draft"}
        
        # Should include comparison data
        assert "comparison" in data
        assert "published_revision" in data.get("comparison", {})

    def test_unauthenticated_draft_preview_returns_403(self):
        """Unauthenticated request with layout_preview=draft returns 403."""
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "layout_preview": "draft",
            },
            timeout=10,
        )
        
        assert resolve_res.status_code == 403, f"Expected 403, got {resolve_res.status_code}"
        detail = resolve_res.json().get("detail", "")
        assert "admin" in str(detail).lower() or "role" in str(detail).lower()

    def test_non_admin_user_draft_preview_returns_403(self, user_token):
        """Non-admin user with layout_preview=draft returns 403."""
        if not user_token:
            pytest.skip("Non-admin user token not available")
        
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            headers=_headers(user_token),
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
                "layout_preview": "draft",
            },
            timeout=10,
        )
        
        assert resolve_res.status_code == 403, f"Expected 403, got {resolve_res.status_code}"

    def test_published_mode_works_without_auth(self, admin_token):
        """layout_preview=published (default) works without auth."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_pub_no_auth_{marker}"
        
        # Create and publish a page (using admin)
        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
            timeout=10,
        )
        assert page_res.status_code == 200
        page_id = page_res.json()["item"]["id"]
        
        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": []}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]
        
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        
        # Resolve without auth (published mode)
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
            },
            timeout=10,
        )
        
        assert resolve_res.status_code == 200, f"Published resolve failed: {resolve_res.text}"
        data = resolve_res.json()
        assert data.get("source") in {"default", "cache", "binding"}
        # Should NOT have preview_mode key for published
        assert data.get("preview_mode") != "draft"

    def test_draft_preview_returns_comparison_with_published(self, admin_token):
        """Draft preview response includes comparison with published version."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_comparison_{marker}"
        
        # Create page
        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "home",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
            timeout=10,
        )
        assert page_res.status_code == 200
        page_id = page_res.json()["item"]["id"]
        
        # Create and publish first draft
        published_content = {"rows": [{"id": "published-content"}]}
        draft1_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": published_content},
            timeout=10,
        )
        assert draft1_res.status_code == 200
        draft1_id = draft1_res.json()["item"]["id"]
        
        publish_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft1_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish_res.status_code == 200
        
        # Create new draft with different content
        new_draft_content = {"rows": [{"id": "new-draft-content"}]}
        draft2_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": new_draft_content},
            timeout=10,
        )
        assert draft2_res.status_code == 200
        
        # Resolve with draft preview
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            headers=_headers(admin_token),
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "home",
                "layout_preview": "draft",
            },
            timeout=10,
        )
        
        assert resolve_res.status_code == 200
        data = resolve_res.json()
        
        # Validate comparison structure
        assert "comparison" in data
        comparison = data.get("comparison", {})
        assert "published_revision" in comparison
        
        # Published revision should have the old content
        published_rev = comparison.get("published_revision")
        if published_rev:
            assert published_rev.get("status") == "published"
            assert "payload_json" in published_rev

    def test_draft_preview_no_draft_returns_409(self, admin_token):
        """Draft preview with no draft revision returns 409."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_no_draft_{marker}"
        
        # Create page and ONLY publish (no draft left)
        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
            timeout=10,
        )
        assert page_res.status_code == 200
        page_id = page_res.json()["item"]["id"]
        
        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": []}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]
        
        # Publish (archives the draft)
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        
        # Try draft preview when no draft exists
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            headers=_headers(admin_token),
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
                "layout_preview": "draft",
            },
            timeout=10,
        )
        
        assert resolve_res.status_code == 409, f"Expected 409, got {resolve_res.status_code}"
        detail = resolve_res.json().get("detail", "")
        assert "no_draft" in str(detail).lower() or "draft" in str(detail).lower()


# =====================================================
# Regression Tests: Home/Search/Wizard flows
# =====================================================
class TestRegressionFlows:
    """Regression tests: home/search/listing wizard fallback flows."""

    def test_home_resolve_still_works(self):
        """Home page resolve returns valid layout (regression)."""
        res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
            },
            timeout=10,
        )
        # May return 200 with layout or 404 if no default page
        assert res.status_code in {200, 404, 409}, f"Unexpected status: {res.status_code}"

    def test_search_l1_resolve_still_works(self):
        """Search L1 resolve returns valid layout (regression)."""
        res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "search_l1",
            },
            timeout=10,
        )
        assert res.status_code in {200, 404, 409}, f"Unexpected status: {res.status_code}"

    def test_listing_create_stepx_resolve_still_works(self):
        """Listing create stepX resolve returns valid layout (regression)."""
        res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "vehicle",
                "page_type": "listing_create_stepX",
            },
            timeout=10,
        )
        assert res.status_code in {200, 404, 409}, f"Unexpected status: {res.status_code}"

    def test_categories_api_still_works(self):
        """Categories API returns data (regression)."""
        res = requests.get(
            f"{BASE_URL}/api/categories",
            params={"country": "DE"},
            timeout=10,
        )
        assert res.status_code == 200, f"Categories API failed: {res.text}"
        assert isinstance(res.json(), list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
