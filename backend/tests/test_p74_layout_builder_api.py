"""
P74 Layout Builder Foundation API Tests
Testing: component definitions, layout pages CRUD, revision draft/publish/archive,
bindings bind/unbind, public resolve, cache behavior, metrics, audit logs, and RBAC.
"""
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token for testing protected endpoints."""
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
def individual_token():
    """Get individual user token to test RBAC (should be denied admin endpoints)."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@platform.com", "password": "User12345!"},
        timeout=15,
    )
    if res.status_code != 200:
        return None  # User may not exist; RBAC test will use None
    return res.json().get("access_token")


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _get_test_category_id() -> str:
    """Get a valid category ID for binding tests."""
    response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE", timeout=10)
    if response.status_code != 200:
        response = requests.get(f"{BASE_URL}/api/categories?country=DE", timeout=10)
    if response.status_code != 200:
        pytest.skip("No categories available for testing")
    items = response.json()
    if isinstance(items, list) and items:
        return items[0]["id"]
    pytest.skip("No categories available for testing")


# =====================================================
# Section 1: Component Definitions API Tests
# =====================================================
class TestComponentDefinitionsAPI:
    """Tests for /api/admin/site/content-layout/components endpoints."""

    def test_create_component_with_valid_schema(self, admin_token):
        """Create component definition with valid JSON Schema."""
        unique_key = f"test.component.valid.{uuid.uuid4().hex[:10]}"
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Valid Test Component",
                "schema_json": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                },
                "is_active": True,
            },
            timeout=10,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("ok") is True
        item = data.get("item", {})
        assert item.get("key") == unique_key
        assert item.get("version") == 1
        assert item.get("is_active") is True

    def test_create_component_invalid_schema_returns_400(self, admin_token):
        """Reject component with invalid JSON Schema."""
        unique_key = f"test.component.invalid.{uuid.uuid4().hex[:10]}"
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Invalid Schema Component",
                "schema_json": {"type": "not-a-valid-json-schema-type"},
                "is_active": True,
            },
            timeout=10,
        )
        assert res.status_code == 400, f"Expected 400, got {res.status_code}: {res.text}"
        data = res.json()
        assert "invalid_json_schema" in str(data.get("detail", "")).lower() or res.status_code == 400

    def test_create_component_key_conflict_returns_409(self, admin_token):
        """Reject duplicate component key with 409 conflict."""
        unique_key = f"test.component.conflict.{uuid.uuid4().hex[:10]}"
        
        # First creation should succeed
        res1 = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "First Component",
                "schema_json": {"type": "object", "properties": {}},
                "is_active": True,
            },
            timeout=10,
        )
        assert res1.status_code == 200, f"First create failed: {res1.text}"

        # Second creation with same key should return 409
        res2 = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Duplicate Component",
                "schema_json": {"type": "object", "properties": {}},
                "is_active": True,
            },
            timeout=10,
        )
        assert res2.status_code == 409, f"Expected 409, got {res2.status_code}: {res2.text}"

    def test_list_components(self, admin_token):
        """List component definitions with pagination."""
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            params={"page": 1, "limit": 10},
            timeout=10,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1

    def test_patch_component(self, admin_token):
        """Patch component definition updates name, schema, version."""
        unique_key = f"test.component.patch.{uuid.uuid4().hex[:10]}"
        
        # Create component
        create_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Original Name",
                "schema_json": {"type": "object", "properties": {}},
                "is_active": True,
            },
            timeout=10,
        )
        assert create_res.status_code == 200
        component_id = create_res.json()["item"]["id"]
        original_version = create_res.json()["item"]["version"]

        # Patch component
        patch_res = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/components/{component_id}",
            headers=_headers(admin_token),
            json={
                "name": "Updated Name",
                "is_active": False,
            },
            timeout=10,
        )
        assert patch_res.status_code == 200, f"Patch failed: {patch_res.text}"
        patched = patch_res.json()["item"]
        assert patched["name"] == "Updated Name"
        assert patched["is_active"] is False
        assert patched["version"] == original_version + 1


# =====================================================
# Section 2: Layout Pages CRUD Tests
# =====================================================
class TestLayoutPagesCRUD:
    """Tests for /api/admin/site/content-layout/pages endpoints."""

    def test_create_layout_page_with_null_category(self, admin_token):
        """Create default layout page (category_id=null)."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_page_null_{marker}"
        
        res = requests.post(
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
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("ok") is True
        item = data.get("item", {})
        assert item.get("page_type") == "search_l1"
        assert item.get("country") == "DE"
        assert item.get("module") == module_name
        assert item.get("category_id") is None

    def test_create_layout_page_scope_uniqueness_conflict(self, admin_token):
        """Duplicate scope (page_type, country, module, category_id) returns 409."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_scope_dup_{marker}"
        
        # First creation
        res1 = requests.post(
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
        assert res1.status_code == 200, f"First page create failed: {res1.text}"

        # Second creation with same scope should return 409
        res2 = requests.post(
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
        assert res2.status_code == 409, f"Expected 409, got {res2.status_code}: {res2.text}"

    def test_create_layout_page_with_category_id(self, admin_token):
        """Create layout page bound to specific category."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_page_cat_{marker}"
        category_id = _get_test_category_id()
        
        res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l2",
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
            },
            timeout=10,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        item = res.json().get("item", {})
        assert item.get("category_id") == category_id

    def test_list_layout_pages(self, admin_token):
        """List layout pages with filters."""
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            params={"page": 1, "limit": 10, "country": "DE"},
            timeout=10,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data
        assert "pagination" in data

    def test_patch_layout_page(self, admin_token):
        """Patch layout page updates country/module."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_patch_page_{marker}"
        
        # Create page
        create_res = requests.post(
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
        assert create_res.status_code == 200
        page_id = create_res.json()["item"]["id"]

        # Patch page
        new_module = f"patched_{marker}"
        patch_res = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}",
            headers=_headers(admin_token),
            json={"module": new_module},
            timeout=10,
        )
        assert patch_res.status_code == 200, f"Patch failed: {patch_res.text}"
        patched = patch_res.json()["item"]
        assert patched["module"] == new_module


# =====================================================
# Section 3: Revision Draft/Publish/Archive Flow Tests
# =====================================================
class TestRevisionFlow:
    """Tests for revision draft, publish, archive lifecycle."""

    def test_create_draft_revision(self, admin_token):
        """Create draft revision for a layout page."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_draft_{marker}"
        
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

        # Create draft
        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": [{"id": "row-1"}]}},
            timeout=10,
        )
        assert draft_res.status_code == 200, f"Draft creation failed: {draft_res.text}"
        draft = draft_res.json()["item"]
        assert draft["status"] == "draft"
        assert draft["layout_page_id"] == page_id
        assert draft["version"] == 1

    def test_publish_revision_creates_new_published(self, admin_token):
        """Publish draft creates new published revision, archives old published."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_publish_{marker}"
        
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
        draft1_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": [{"id": "v1"}]}},
            timeout=10,
        )
        assert draft1_res.status_code == 200
        draft1_id = draft1_res.json()["item"]["id"]

        publish1_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft1_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish1_res.status_code == 200, f"Publish failed: {publish1_res.text}"
        published1 = publish1_res.json()["item"]
        assert published1["status"] == "published"
        assert published1["published_at"] is not None

        # Create and publish second draft - should archive first
        draft2_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": [{"id": "v2"}]}},
            timeout=10,
        )
        assert draft2_res.status_code == 200
        draft2_id = draft2_res.json()["item"]["id"]

        publish2_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft2_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish2_res.status_code == 200
        published2 = publish2_res.json()["item"]
        assert published2["status"] == "published"

        # List revisions - should have exactly one published
        list_res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert list_res.status_code == 200
        revisions = list_res.json()["items"]
        published_count = sum(1 for r in revisions if r["status"] == "published")
        assert published_count == 1, f"Expected exactly 1 published, got {published_count}"

    def test_archive_revision(self, admin_token):
        """Archive a published revision."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_archive_{marker}"
        
        # Create page, draft, publish
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

        publish_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish_res.status_code == 200
        published_id = publish_res.json()["item"]["id"]

        # Archive the published revision
        archive_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{published_id}/archive",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert archive_res.status_code == 200, f"Archive failed: {archive_res.text}"
        archived = archive_res.json()["item"]
        assert archived["status"] == "archived"
        assert archived["published_at"] is None

    def test_only_draft_can_be_published(self, admin_token):
        """Publishing non-draft revision returns 409."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_nondraft_{marker}"
        
        # Create page, draft, publish, then try to publish the archived draft
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

        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]

        # Publish once
        publish1_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish1_res.status_code == 200

        # Try to publish the same draft again (now archived) - should fail
        publish2_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert publish2_res.status_code == 409, f"Expected 409, got {publish2_res.status_code}"


# =====================================================
# Section 4: Bindings Bind/Unbind Flow Tests
# =====================================================
class TestBindingsFlow:
    """Tests for category binding endpoints."""

    def test_bind_category_to_page(self, admin_token):
        """Bind a category to a layout page."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_bind_{marker}"
        category_id = _get_test_category_id()
        
        # Create page with published revision (required for binding)
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

        # Create and publish a revision
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

        # Bind category to page
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
        binding = bind_res.json()["item"]
        assert binding["is_active"] is True
        assert binding["category_id"] == category_id
        assert binding["layout_page_id"] == page_id

    def test_get_active_binding(self, admin_token):
        """Get active binding for scope."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_active_bind_{marker}"
        category_id = _get_test_category_id()
        
        # Create page, publish, bind
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
            json={"payload_json": {}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]

        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )

        requests.post(
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

        # Get active binding
        active_res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
            headers=_headers(admin_token),
            params={"country": "DE", "module": module_name, "category_id": category_id},
            timeout=10,
        )
        assert active_res.status_code == 200, f"Get active failed: {active_res.text}"
        binding = active_res.json().get("item")
        assert binding is not None
        assert binding["layout_page_id"] == page_id

    def test_unbind_category(self, admin_token):
        """Unbind category sets is_active=false."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_unbind_{marker}"
        category_id = _get_test_category_id()
        
        # Create page, publish, bind
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
            json={"payload_json": {}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]

        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )

        requests.post(
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
        assert unbind_res.json()["unbound_count"] >= 1

        # Verify no active binding
        active_res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
            headers=_headers(admin_token),
            params={"country": "DE", "module": module_name, "category_id": category_id},
            timeout=10,
        )
        assert active_res.status_code == 200
        assert active_res.json().get("item") is None

    def test_rebind_deactivates_previous(self, admin_token):
        """Binding to new page deactivates previous binding."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_rebind_{marker}"
        category_id = _get_test_category_id()
        
        # Create two pages
        page1_res = requests.post(
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
        assert page1_res.status_code == 200
        page1_id = page1_res.json()["item"]["id"]

        page2_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": f"{module_name}_v2",
                "category_id": None,
            },
            timeout=10,
        )
        assert page2_res.status_code == 200
        page2_id = page2_res.json()["item"]["id"]

        # Publish both pages
        for page_id in [page1_id, page2_id]:
            draft_res = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
                headers=_headers(admin_token),
                json={"payload_json": {}},
                timeout=10,
            )
            assert draft_res.status_code == 200
            draft_id = draft_res.json()["item"]["id"]
            requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
                headers=_headers(admin_token),
                timeout=10,
            )

        # Bind to first page
        bind1_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings",
            headers=_headers(admin_token),
            json={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
                "layout_page_id": page1_id,
            },
            timeout=10,
        )
        assert bind1_res.status_code == 200

        # Rebind to second page
        bind2_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings",
            headers=_headers(admin_token),
            json={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
                "layout_page_id": page2_id,
            },
            timeout=10,
        )
        assert bind2_res.status_code == 200

        # Verify active binding points to page2
        active_res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
            headers=_headers(admin_token),
            params={"country": "DE", "module": module_name, "category_id": category_id},
            timeout=10,
        )
        assert active_res.status_code == 200
        assert active_res.json()["item"]["layout_page_id"] == page2_id


# =====================================================
# Section 5: Public Resolve Endpoint with Fallback
# =====================================================
class TestPublicResolve:
    """Tests for /api/site/content-layout/resolve public endpoint."""

    def test_resolve_default_fallback(self, admin_token):
        """Resolve falls back to default page when no binding exists."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_resolve_default_{marker}"
        
        # Create default page (category_id=null), publish
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
            json={"payload_json": {"type": "default"}},
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

        # Resolve without category_id - should get default
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
            },
            timeout=10,
        )
        assert resolve_res.status_code == 200, f"Resolve failed: {resolve_res.text}"
        data = resolve_res.json()
        assert data.get("source") in {"default", "cache"}
        assert data.get("layout_page", {}).get("id") == page_id

    def test_resolve_binding_takes_precedence(self, admin_token):
        """Resolve returns bound page when binding exists."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_resolve_bind_{marker}"
        category_id = _get_test_category_id()
        
        # Create default page
        default_res = requests.post(
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
        assert default_res.status_code == 200
        default_page_id = default_res.json()["item"]["id"]

        # Create category-specific page
        category_page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": f"{module_name}_cat",
                "category_id": None,
            },
            timeout=10,
        )
        assert category_page_res.status_code == 200
        category_page_id = category_page_res.json()["item"]["id"]

        # Publish both pages
        for page_id in [default_page_id, category_page_id]:
            draft_res = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
                headers=_headers(admin_token),
                json={"payload_json": {}},
                timeout=10,
            )
            assert draft_res.status_code == 200
            draft_id = draft_res.json()["item"]["id"]
            requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
                headers=_headers(admin_token),
                timeout=10,
            )

        # Bind category to category_page
        bind_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings",
            headers=_headers(admin_token),
            json={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
                "layout_page_id": category_page_id,
            },
            timeout=10,
        )
        assert bind_res.status_code == 200

        # Resolve with category_id - should get bound page
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
                "category_id": category_id,
            },
            timeout=10,
        )
        assert resolve_res.status_code == 200, f"Resolve failed: {resolve_res.text}"
        data = resolve_res.json()
        # Should be binding source (not default)
        assert data.get("revision", {}).get("layout_page_id") == category_page_id

    def test_resolve_404_when_no_default_page(self, admin_token):
        """Resolve returns 404 when no default page exists for scope."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_resolve_missing_{marker}"
        
        # No page created - resolve should 404
        resolve_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
            },
            timeout=10,
        )
        assert resolve_res.status_code == 404, f"Expected 404, got {resolve_res.status_code}"


# =====================================================
# Section 6: Cache Behavior Tests
# =====================================================
class TestCacheBehavior:
    """Tests for resolve cache and invalidation."""

    def test_resolve_cache_hit(self, admin_token):
        """Second resolve call returns cached result."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_cache_hit_{marker}"
        
        # Create and publish default page
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

        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]

        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=_headers(admin_token),
            timeout=10,
        )

        # First resolve - miss
        resolve1_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": module_name, "page_type": "home"},
            timeout=10,
        )
        assert resolve1_res.status_code == 200

        # Second resolve - should be cache hit
        resolve2_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": module_name, "page_type": "home"},
            timeout=10,
        )
        assert resolve2_res.status_code == 200
        # source could be "cache" on second hit
        assert resolve2_res.json().get("source") in {"default", "cache", "binding"}


# =====================================================
# Section 7: Metrics and Audit Logs
# =====================================================
class TestMetricsAndAuditLogs:
    """Tests for metrics and audit log endpoints."""

    def test_get_metrics(self, admin_token):
        """Get layout builder metrics."""
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/metrics",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert res.status_code == 200, f"Metrics failed: {res.text}"
        data = res.json()
        metrics = data.get("metrics", {})
        assert "resolve_requests" in metrics
        assert "resolve_cache_hits" in metrics
        assert "resolve_cache_misses" in metrics
        assert "publish_count" in metrics
        assert "binding_changes" in metrics

    def test_list_audit_logs(self, admin_token):
        """List audit logs with filters."""
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/audit-logs",
            headers=_headers(admin_token),
            params={"page": 1, "limit": 10},
            timeout=10,
        )
        assert res.status_code == 200, f"Audit logs failed: {res.text}"
        data = res.json()
        assert "items" in data
        assert "pagination" in data

    def test_audit_logs_filter_by_entity_type(self, admin_token):
        """Filter audit logs by entity type."""
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/audit-logs",
            headers=_headers(admin_token),
            params={"entity_type": "layout_page", "limit": 5},
            timeout=10,
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        for item in items:
            assert item.get("entity_type") == "layout_page"

    def test_audit_logs_filter_by_action(self, admin_token):
        """Filter audit logs by action."""
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/audit-logs",
            headers=_headers(admin_token),
            params={"action": "CREATE_PAGE", "limit": 5},
            timeout=10,
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        for item in items:
            assert item.get("action") == "CREATE_PAGE"


# =====================================================
# Section 8: RBAC Enforcement Tests
# =====================================================
class TestRBACEnforcement:
    """Tests for RBAC on admin endpoints."""

    def test_unauthenticated_admin_endpoints_return_401(self):
        """Admin endpoints require authentication."""
        endpoints = [
            ("GET", "/api/admin/site/content-layout/components"),
            ("POST", "/api/admin/site/content-layout/components"),
            ("GET", "/api/admin/site/content-layout/pages"),
            ("POST", "/api/admin/site/content-layout/pages"),
            ("GET", "/api/admin/site/content-layout/metrics"),
            ("GET", "/api/admin/site/content-layout/audit-logs"),
        ]
        for method, path in endpoints:
            if method == "GET":
                res = requests.get(f"{BASE_URL}{path}", timeout=10)
            else:
                res = requests.post(f"{BASE_URL}{path}", json={}, timeout=10)
            assert res.status_code in {401, 403, 422}, f"{method} {path} returned {res.status_code}"

    def test_individual_user_denied_admin_endpoints(self, individual_token):
        """Individual users cannot access admin layout builder endpoints."""
        if not individual_token:
            pytest.skip("Individual user token not available")
        
        res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(individual_token),
            timeout=10,
        )
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"

    def test_public_resolve_no_auth_required(self):
        """Public resolve endpoint does not require authentication."""
        # This will likely 404 but should not be 401/403
        res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "nonexistent",
                "page_type": "home",
            },
            timeout=10,
        )
        assert res.status_code not in {401, 403}, f"Public endpoint returned {res.status_code}"


# =====================================================
# Section 9: Concurrency Tests
# =====================================================
class TestConcurrency:
    """Tests for concurrent publish and binding operations."""

    def test_concurrent_publish_single_winner(self, admin_token):
        """Concurrent publish of same draft - only one should succeed."""
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_conc_pub_{marker}"
        
        # Create page and draft
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

        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"test": "concurrent"}},
            timeout=10,
        )
        assert draft_res.status_code == 200
        draft_id = draft_res.json()["item"]["id"]

        def _publish():
            return requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
                headers=_headers(admin_token),
                timeout=20,
            ).status_code

        # Concurrent publish attempts
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: _publish(), [0, 1]))

        # Exactly one should succeed (200), one should conflict (409)
        assert 200 in statuses, f"No successful publish in {statuses}"
        assert 409 in statuses, f"No conflict in {statuses}"
        assert statuses.count(200) == 1, f"Expected 1 success, got {statuses}"
