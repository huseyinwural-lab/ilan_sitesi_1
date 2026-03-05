"""
P3 Feature Tests: Schema Form Editor, Visual Diff, and Step-Based Wizard Visibility
====================================================================================
P3.1: Admin builder component props editor renders schema-driven typed controls
P3.2: Diff summary counts render and row/column/component highlighting
P3.3: Listing wizard runtime payload filtered by step rules
"""

import os
import pytest
import requests
import uuid
import json
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
        timeout=60,
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code}")
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Auth headers for admin requests"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestP31SchemaFormEditor:
    """P3.1: Component props editor with schema-driven typed controls"""

    def test_list_components_returns_schema_json(self, admin_headers):
        """Verify component definitions include schema_json"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            params={"page": 1, "limit": 50},
            timeout=45,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        items = data.get("items", [])
        
        # Check if we have components with schema_json
        for item in items:
            assert "schema_json" in item, f"Component {item.get('key')} missing schema_json"
            schema = item.get("schema_json")
            assert isinstance(schema, dict), f"schema_json should be dict, got {type(schema)}"
        print(f"Found {len(items)} components with schema_json")

    def test_create_component_with_typed_schema(self, admin_headers):
        """Create component with string/number/boolean/enum schema properties"""
        unique_key = f"test.p31.typed.{uuid.uuid4().hex[:8]}"
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string", "title": "Başlık"},
                "count": {"type": "number", "title": "Sayı"},
                "is_active": {"type": "boolean", "title": "Aktif Mi"},
                "placement": {
                    "type": "string",
                    "title": "Placement",
                    "enum": ["TOP", "MIDDLE", "BOTTOM"]
                }
            },
            "additionalProperties": False
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            json={
                "key": unique_key,
                "name": f"P3.1 Test Component {unique_key}",
                "schema_json": schema,
                "is_active": True,
            },
            timeout=45,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        created = resp.json().get("item", {})
        
        # Verify schema was saved correctly
        saved_schema = created.get("schema_json", {})
        props = saved_schema.get("properties", {})
        
        assert "title" in props, "title property missing from schema"
        assert props["title"]["type"] == "string"
        
        assert "count" in props, "count property missing from schema"
        assert props["count"]["type"] == "number"
        
        assert "is_active" in props, "is_active property missing from schema"
        assert props["is_active"]["type"] == "boolean"
        
        assert "placement" in props, "placement property missing from schema"
        assert "enum" in props["placement"], "placement should have enum"
        assert props["placement"]["enum"] == ["TOP", "MIDDLE", "BOTTOM"]
        
        print(f"Created component {unique_key} with typed schema: string/number/boolean/enum")

    def test_patch_component_schema_updates_correctly(self, admin_headers):
        """Verify schema updates are persisted"""
        # First create
        unique_key = f"test.p31.patch.{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=admin_headers,
            json={
                "key": unique_key,
                "name": f"P3.1 Patch Test {unique_key}",
                "schema_json": {"type": "object", "properties": {"foo": {"type": "string"}}},
                "is_active": True,
            },
            timeout=45,
        )
        assert create_resp.status_code == 200
        component_id = create_resp.json().get("item", {}).get("id")
        
        # Patch with updated schema
        new_schema = {
            "type": "object",
            "properties": {
                "foo": {"type": "string"},
                "bar": {"type": "number"},
                "enabled": {"type": "boolean"},
            }
        }
        patch_resp = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/components/{component_id}",
            headers=admin_headers,
            json={"schema_json": new_schema},
            timeout=45,
        )
        assert patch_resp.status_code == 200, f"Patch failed: {patch_resp.text}"
        
        patched = patch_resp.json().get("item", {})
        patched_props = patched.get("schema_json", {}).get("properties", {})
        
        assert "foo" in patched_props
        assert "bar" in patched_props
        assert "enabled" in patched_props
        assert patched_props["bar"]["type"] == "number"
        assert patched_props["enabled"]["type"] == "boolean"
        
        print(f"Patched component {component_id} - schema updated with new properties")


class TestP32VisualDiffHighlighting:
    """P3.2: Draft-Published visual diff (row/column/component highlighting)"""

    def test_diff_summary_in_revision_comparison(self, admin_headers):
        """Create page with draft and published, verify diff is available"""
        unique_module = f"p32_diff_{uuid.uuid4().hex[:6]}"
        
        # Create page
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "home",
                "country": "DE",
                "module": unique_module,
                "category_id": None,
            },
            timeout=45,
        )
        assert page_resp.status_code == 200, f"Page create failed: {page_resp.text}"
        page_id = page_resp.json().get("item", {}).get("id")
        
        # Create initial draft
        initial_payload = {
            "rows": [{
                "id": "row-initial-1",
                "columns": [{
                    "id": "col-initial-1",
                    "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                    "components": [{
                        "id": "cmp-initial-1",
                        "key": "home.default-content",
                        "props": {"note": "original"}
                    }]
                }]
            }]
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json={"payload_json": initial_payload},
            timeout=45,
        )
        assert draft_resp.status_code == 200
        draft_id = draft_resp.json().get("item", {}).get("id")
        
        # Publish
        publish_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=admin_headers,
            timeout=45,
        )
        assert publish_resp.status_code == 200, f"Publish failed: {publish_resp.text}"
        
        # Get revisions to find new draft
        revisions_resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers=admin_headers,
            timeout=45,
        )
        assert revisions_resp.status_code == 200
        revisions = revisions_resp.json().get("items", [])
        
        new_draft = next((r for r in revisions if r.get("status") == "draft"), None)
        published_rev = next((r for r in revisions if r.get("status") == "published"), None)
        
        assert new_draft is not None, "New draft should be created after publish"
        assert published_rev is not None, "Published revision should exist"
        
        # Update draft with different payload (to create diff)
        modified_payload = {
            "rows": [
                {
                    "id": "row-initial-1",
                    "columns": [{
                        "id": "col-initial-1",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [{
                            "id": "cmp-initial-1",
                            "key": "home.default-content",
                            "props": {"note": "modified"}  # Changed prop
                        }]
                    }]
                },
                {  # New row
                    "id": "row-new-2",
                    "columns": [{
                        "id": "col-new-2",
                        "width": {"desktop": 6, "tablet": 12, "mobile": 12},
                        "components": []
                    }]
                }
            ]
        }
        
        patch_resp = requests.patch(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{new_draft['id']}/draft",
            headers=admin_headers,
            json={"payload_json": modified_payload},
            timeout=45,
        )
        assert patch_resp.status_code == 200
        
        # Resolve with draft preview to verify comparison info
        resolve_resp = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            headers=admin_headers,
            params={
                "country": "DE",
                "module": unique_module,
                "page_type": "home",
                "layout_preview": "draft",
            },
            timeout=45,
        )
        assert resolve_resp.status_code == 200, f"Resolve failed: {resolve_resp.text}"
        resolve_data = resolve_resp.json()
        
        # Should have comparison data
        assert "comparison" in resolve_data, "Draft preview should include comparison"
        assert resolve_data.get("draft_available") == True
        
        print(f"P3.2: Diff comparison available - draft has changes vs published")
        print(f"  - Published revision: {published_rev.get('id', 'N/A')}")
        print(f"  - Draft revision: {new_draft.get('id', 'N/A')}")


class TestP33ListingWizardStepVisibility:
    """P3.3: Listing wizard step-based visibility rules"""

    def test_listing_create_page_allowed_components(self, admin_headers):
        """Verify only allowed components can be added to listing_create_stepX pages"""
        unique_module = f"p33_wizard_{uuid.uuid4().hex[:6]}"
        
        # Create listing_create_stepX page
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": unique_module,
                "category_id": None,
            },
            timeout=45,
        )
        assert page_resp.status_code == 200, f"Page create failed: {page_resp.text}"
        page_id = page_resp.json().get("item", {}).get("id")
        
        # Test with allowed components
        allowed_payload = {
            "rows": [{
                "id": "row-1",
                "columns": [{
                    "id": "col-1",
                    "width": {"desktop": 12},
                    "components": [
                        {"id": "cmp-1", "key": "listing.create.default-content", "props": {}},
                        {"id": "cmp-2", "key": "shared.text-block", "props": {"title": "Test", "body": "Test body"}},
                        {"id": "cmp-3", "key": "shared.ad-slot", "props": {"placement": "AD_LOGIN_1"}},
                    ]
                }]
            }]
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json={"payload_json": allowed_payload},
            timeout=45,
        )
        assert draft_resp.status_code == 200, f"Allowed payload should be accepted: {draft_resp.text}"
        print("P3.3: Allowed components (listing.create.default-content, shared.text-block, shared.ad-slot) accepted")

    def test_listing_create_page_disallowed_component_rejected(self, admin_headers):
        """Disallowed components should be rejected with 400"""
        unique_module = f"p33_reject_{uuid.uuid4().hex[:6]}"
        
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": unique_module,
                "category_id": None,
            },
            timeout=45,
        )
        assert page_resp.status_code == 200
        page_id = page_resp.json().get("item", {}).get("id")
        
        # Try with disallowed component
        disallowed_payload = {
            "rows": [{
                "id": "row-1",
                "columns": [{
                    "id": "col-1",
                    "width": {"desktop": 12},
                    "components": [
                        {"id": "cmp-1", "key": "some.disallowed.component", "props": {}},
                    ]
                }]
            }]
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json={"payload_json": disallowed_payload},
            timeout=45,
        )
        assert draft_resp.status_code == 400, f"Disallowed component should return 400, got {draft_resp.status_code}"
        assert "not_allowed" in draft_resp.text.lower() or "disallowed" in draft_resp.text.lower() or "listing_create_component_not_allowed" in draft_resp.text
        print("P3.3: Disallowed component correctly rejected with 400")

    def test_listing_create_disallowed_props_rejected(self, admin_headers):
        """Props not in whitelist should be rejected"""
        unique_module = f"p33_props_{uuid.uuid4().hex[:6]}"
        
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": unique_module,
                "category_id": None,
            },
            timeout=45,
        )
        assert page_resp.status_code == 200
        page_id = page_resp.json().get("item", {}).get("id")
        
        # Try shared.text-block with disallowed prop
        bad_props_payload = {
            "rows": [{
                "id": "row-1",
                "columns": [{
                    "id": "col-1",
                    "width": {"desktop": 12},
                    "components": [
                        {"id": "cmp-1", "key": "shared.text-block", "props": {
                            "title": "OK",
                            "body": "OK",
                            "forbidden_prop": "should fail"  # Not allowed
                        }},
                    ]
                }]
            }]
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json={"payload_json": bad_props_payload},
            timeout=45,
        )
        assert draft_resp.status_code == 400, f"Disallowed props should return 400, got {draft_resp.status_code}"
        print("P3.3: Disallowed props correctly rejected with 400")

    def test_listing_default_content_preserved(self, admin_headers):
        """listing.create.default-content must always be preserved"""
        unique_module = f"p33_preserve_{uuid.uuid4().hex[:6]}"
        
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": unique_module,
                "category_id": None,
            },
            timeout=45,
        )
        assert page_resp.status_code == 200
        page_id = page_resp.json().get("item", {}).get("id")
        
        # Valid payload with listing.create.default-content
        valid_payload = {
            "rows": [{
                "id": "row-main",
                "columns": [{
                    "id": "col-main",
                    "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                    "components": [
                        {"id": "cmp-default", "key": "listing.create.default-content", "props": {}},
                    ]
                }]
            }]
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json={"payload_json": valid_payload},
            timeout=45,
        )
        assert draft_resp.status_code == 200
        draft_id = draft_resp.json().get("item", {}).get("id")
        
        # Publish
        pub_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
            headers=admin_headers,
            timeout=45,
        )
        assert pub_resp.status_code == 200
        
        # Resolve and verify
        resolve_resp = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": unique_module,
                "page_type": "listing_create_stepX",
            },
            timeout=45,
        )
        assert resolve_resp.status_code == 200
        resolved = resolve_resp.json()
        
        # Check listing.create.default-content is in the payload
        revision_payload = resolved.get("revision", {}).get("payload_json", {})
        rows = revision_payload.get("rows", [])
        
        has_default = False
        for row in rows:
            for col in row.get("columns", []):
                for comp in col.get("components", []):
                    if comp.get("key") == "listing.create.default-content":
                        has_default = True
                        break
        
        assert has_default, "listing.create.default-content should be preserved in resolved payload"
        print("P3.3: listing.create.default-content preserved in wizard runtime payload")


class TestRegressionHomepageSearchAdmin:
    """Regression: Ensure home/search runtime and admin builder still work"""

    def test_home_resolve_still_works(self, admin_headers):
        """Home page resolve should work"""
        resp = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": "global", "page_type": "home"},
            timeout=45,
        )
        # May be 404 if no page exists, or 200/409 if exists
        assert resp.status_code in [200, 404, 409], f"Unexpected status: {resp.status_code}"
        print(f"Home resolve returned: {resp.status_code}")

    def test_search_l1_resolve_still_works(self, admin_headers):
        """Search L1 resolve should work"""
        resp = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": "global", "page_type": "search_l1"},
            timeout=45,
        )
        assert resp.status_code in [200, 404, 409], f"Unexpected status: {resp.status_code}"
        print(f"Search L1 resolve returned: {resp.status_code}")

    def test_admin_pages_list_works(self, admin_headers):
        """Admin can list layout pages"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            params={"page": 1, "limit": 10},
            timeout=45,
        )
        assert resp.status_code == 200, f"Admin pages list failed: {resp.status_code}"
        data = resp.json()
        assert "items" in data
        assert "pagination" in data
        print(f"Admin pages list: {len(data.get('items', []))} items")

    def test_drag_drop_width_controls_no_regression(self, admin_headers):
        """Verify width controls work (no regression from P2)"""
        unique_module = f"regress_dd_{uuid.uuid4().hex[:6]}"
        
        # Create page
        page_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            json={
                "page_type": "home",
                "country": "DE",
                "module": unique_module,
            },
            timeout=45,
        )
        assert page_resp.status_code == 200
        page_id = page_resp.json().get("item", {}).get("id")
        
        # Create draft with specific width values
        payload_with_widths = {
            "rows": [{
                "id": "row-1",
                "columns": [
                    {
                        "id": "col-1",
                        "width": {"desktop": 6, "tablet": 12, "mobile": 12},
                        "components": []
                    },
                    {
                        "id": "col-2",
                        "width": {"desktop": 6, "tablet": 6, "mobile": 12},
                        "components": []
                    }
                ]
            }]
        }
        
        draft_resp = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=admin_headers,
            json={"payload_json": payload_with_widths},
            timeout=45,
        )
        assert draft_resp.status_code == 200
        
        saved_payload = draft_resp.json().get("item", {}).get("payload_json", {})
        cols = saved_payload.get("rows", [{}])[0].get("columns", [])
        
        assert len(cols) == 2, "Should have 2 columns"
        assert cols[0].get("width", {}).get("desktop") == 6
        assert cols[1].get("width", {}).get("desktop") == 6
        print("Width controls work correctly - no regression")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
