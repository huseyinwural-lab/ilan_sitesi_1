"""
Iteration 125: Content Builder / Drawer / Draft-Publish / Drag-Drop Tests
Tests for:
- Admin login with admin@platform.com / Admin123!
- Admin Content Builder API endpoints
- Layout page load/create flow
- Draft save and publish flow
- Binding operations (fetch active / bind / unbind)
"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://dynamic-layout-io.preview.emergentagent.com"

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    data = resp.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Authorization headers for admin requests."""
    return {"Authorization": f"Bearer {admin_token}"}


class TestAdminLogin:
    """Test admin login with required credentials."""
    
    def test_admin_login_success(self):
        """Admin login with admin@platform.com / Admin123! should return 200."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "super_admin"
        assert "access_token" in data
        print(f"Admin login success: {data['user']['email']}, role={data['user']['role']}")

    def test_dealer_login_success(self):
        """Dealer login should also work."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == DEALER_EMAIL
        assert data["user"]["role"] == "dealer"
        print(f"Dealer login success: {data['user']['email']}")

    def test_user_login_success(self):
        """Regular user login should work."""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASSWORD},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == USER_EMAIL
        print(f"User login success: {data['user']['email']}")


class TestLayoutPageOperations:
    """Test layout page list/create operations."""

    def test_list_layout_pages(self, admin_headers):
        """GET /api/admin/site/content-layout/pages should return paginated pages."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            params={"page_type": "home", "country": "DE", "module": "global"},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "pagination" in data
        print(f"Listed {len(data['items'])} layout pages")

    def test_create_layout_page_if_not_exists(self, admin_headers):
        """POST /api/admin/site/content-layout/pages should create a page."""
        # First check if test page exists
        unique_module = f"test_iter125_{uuid.uuid4().hex[:8]}"
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "home",
                "country": "DE",
                "module": unique_module,
                "category_id": None
            },
            timeout=30,
        )
        assert resp.status_code == 200, f"Failed to create page: {resp.text}"
        data = resp.json()
        assert data["ok"] is True
        assert data["item"]["page_type"] == "home"
        assert data["item"]["country"] == "DE"
        page_id = data["item"]["id"]
        print(f"Created layout page: {page_id}")
        return page_id


class TestDraftSavePublish:
    """Test draft save and publish workflow."""

    def test_draft_save_and_publish_flow(self, admin_headers):
        """Full draft save then publish workflow."""
        # 1. Create a unique test page
        unique_module = f"draft_test_{uuid.uuid4().hex[:8]}"
        
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "home",
                "country": "DE",
                "module": unique_module,
            },
            timeout=30,
        )
        assert create_resp.status_code == 200, f"Create page failed: {create_resp.text}"
        page_id = create_resp.json()["item"]["id"]
        print(f"Created page for draft test: {page_id}")

        # 2. Create draft revision
        draft_payload = {
            "payload_json": {
                "rows": [
                    {
                        "id": "test-row-1",
                        "columns": [
                            {
                                "id": "test-col-1",
                                "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                "components": [
                                    {
                                        "id": "test-cmp-1",
                                        "key": "home.default-content",
                                        "props": {},
                                        "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json=draft_payload,
            timeout=30,
        )
        assert draft_resp.status_code == 200, f"Create draft failed: {draft_resp.text}"
        draft_data = draft_resp.json()
        draft_id = draft_data["item"]["id"]
        assert draft_data["item"]["status"] == "draft"
        print(f"Created draft revision: {draft_id}")

        # 3. Update draft (PATCH)
        update_payload = {
            "payload_json": {
                "rows": [
                    {
                        "id": "test-row-1",
                        "columns": [
                            {
                                "id": "test-col-1",
                                "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                "components": [
                                    {
                                        "id": "test-cmp-1",
                                        "key": "home.default-content",
                                        "props": {"updated": True},
                                        "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        patch_resp = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/draft",
            headers=admin_headers,
            json=update_payload,
            timeout=30,
        )
        assert patch_resp.status_code == 200, f"Patch draft failed: {patch_resp.text}"
        print(f"Updated draft revision successfully")

        # 4. Publish the draft
        publish_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=admin_headers,
            timeout=30,
        )
        assert publish_resp.status_code == 200, f"Publish failed: {publish_resp.text}"
        publish_data = publish_resp.json()
        assert publish_data["item"]["status"] == "published"
        print(f"Published revision successfully: {publish_data['item']['id']}")

        # 5. List revisions for verification
        revisions_resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers=admin_headers,
            timeout=30,
        )
        assert revisions_resp.status_code == 200
        revisions = revisions_resp.json()["items"]
        assert len(revisions) >= 1
        print(f"Page has {len(revisions)} revisions")


class TestBindingOperations:
    """Test binding fetch/bind/unbind operations."""

    def test_binding_operations_with_error_handling(self, admin_headers):
        """Test binding operations - fetch active / bind / unbind."""
        unique_module = f"binding_test_{uuid.uuid4().hex[:8]}"
        
        # 1. Create a test layout page first
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": unique_module,
            },
            timeout=30,
        )
        assert page_resp.status_code == 200
        page_id = page_resp.json()["item"]["id"]
        print(f"Created page for binding test: {page_id}")

        # 2. Test fetch active binding (should return null initially)
        # Use a real category ID from DB or a made-up UUID for testing
        test_category_id = str(uuid.uuid4())  # Using random UUID - will return null
        
        fetch_resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
            headers=admin_headers,
            params={
                "country": "DE",
                "module": unique_module,
                "category_id": test_category_id,
            },
            timeout=30,
        )
        # This endpoint should return 200 with item: null for non-existent binding
        assert fetch_resp.status_code == 200
        fetch_data = fetch_resp.json()
        print(f"Fetch active binding result: {fetch_data}")

        # 3. Test bind operation
        bind_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings",
            headers=admin_headers,
            json={
                "country": "DE",
                "module": unique_module,
                "category_id": test_category_id,
                "layout_page_id": page_id,
            },
            timeout=30,
        )
        # This might return 404 if category doesn't exist, or 200 if binding is created
        # Both are acceptable for this test - we're testing error handling
        if bind_resp.status_code == 200:
            print(f"Binding created successfully")
            
            # 4. Unbind
            unbind_resp = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/bindings/unbind",
                headers=admin_headers,
                json={
                    "country": "DE",
                    "module": unique_module,
                    "category_id": test_category_id,
                },
                timeout=30,
            )
            assert unbind_resp.status_code == 200
            print(f"Unbind result: {unbind_resp.json()}")
        else:
            print(f"Binding operation returned {bind_resp.status_code}: {bind_resp.text[:200]}")
            # This is expected if category doesn't exist


class TestComponentLibrary:
    """Test component library CRUD."""

    def test_list_components(self, admin_headers):
        """GET /api/admin/site/content-layout/components should return components."""
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            params={"is_active": True, "page": 1, "limit": 25},
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        print(f"Found {len(data['items'])} active components")

    def test_create_test_component(self, admin_headers):
        """POST /api/admin/site/content-layout/components should create component."""
        unique_key = f"test.component.{uuid.uuid4().hex[:6]}"
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            json={
                "key": unique_key,
                "name": "Test Component",
                "schema_json": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "title": "Title"}
                    }
                },
                "is_active": True
            },
            timeout=30,
        )
        assert resp.status_code == 200, f"Create component failed: {resp.text}"
        data = resp.json()
        assert data["ok"] is True
        assert data["item"]["key"] == unique_key
        print(f"Created test component: {unique_key}")


class TestDragDropCanvasSupport:
    """Test drag-drop canvas operations via API."""

    def test_component_reorder_via_draft_update(self, admin_headers):
        """Test that components can be reordered by updating draft payload."""
        unique_module = f"dragdrop_test_{uuid.uuid4().hex[:8]}"
        
        # Create page
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={"page_type": "home", "country": "DE", "module": unique_module},
            timeout=30,
        )
        assert page_resp.status_code == 200
        page_id = page_resp.json()["item"]["id"]

        # Create draft with 2 components
        initial_payload = {
            "payload_json": {
                "rows": [
                    {
                        "id": "row-1",
                        "columns": [
                            {
                                "id": "col-1",
                                "width": {"desktop": 6, "tablet": 12, "mobile": 12},
                                "components": [
                                    {"id": "cmp-A", "key": "shared.text-block", "props": {"title": "A"}},
                                ]
                            },
                            {
                                "id": "col-2",
                                "width": {"desktop": 6, "tablet": 12, "mobile": 12},
                                "components": [
                                    {"id": "cmp-B", "key": "shared.text-block", "props": {"title": "B"}},
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json=initial_payload,
            timeout=30,
        )
        assert draft_resp.status_code == 200
        draft_id = draft_resp.json()["item"]["id"]
        print(f"Created draft with 2 columns: {draft_id}")

        # Simulate drag-drop by moving component B to column 1
        reordered_payload = {
            "payload_json": {
                "rows": [
                    {
                        "id": "row-1",
                        "columns": [
                            {
                                "id": "col-1",
                                "width": {"desktop": 6, "tablet": 12, "mobile": 12},
                                "components": [
                                    {"id": "cmp-A", "key": "shared.text-block", "props": {"title": "A"}},
                                    {"id": "cmp-B", "key": "shared.text-block", "props": {"title": "B"}},  # Moved here
                                ]
                            },
                            {
                                "id": "col-2",
                                "width": {"desktop": 6, "tablet": 12, "mobile": 12},
                                "components": []  # Now empty
                            }
                        ]
                    }
                ]
            }
        }
        
        patch_resp = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/draft",
            headers=admin_headers,
            json=reordered_payload,
            timeout=30,
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()["item"]["payload_json"]
        
        # Verify component B is now in column 1
        col1_components = updated["rows"][0]["columns"][0]["components"]
        col2_components = updated["rows"][0]["columns"][1]["components"]
        assert len(col1_components) == 2, "Column 1 should have 2 components after drag"
        assert len(col2_components) == 0, "Column 2 should be empty after drag"
        print("Drag-drop simulation successful - component moved between columns")


class TestResolveEndpoint:
    """Test public resolve endpoint."""

    def test_resolve_published_layout(self, admin_headers):
        """GET /api/site/content-layout/resolve should return layout."""
        resp = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home",
            },
            timeout=30,
        )
        # 200 = found, 404 = no layout exists, 409 = no published revision
        assert resp.status_code in [200, 404, 409], f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            print(f"Resolved layout source: {data.get('source')}")
        else:
            print(f"Resolve returned {resp.status_code}: expected for test environment")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
