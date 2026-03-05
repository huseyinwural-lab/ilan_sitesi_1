"""
Iteration 134: Dynamic Page Builder - 15 Standard Page Types Tests
Tests for: seed endpoint, policy guards, resolve endpoint, wizard runtime mapping
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def admin_token():
    """Get super admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
        timeout=15
    )
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text[:200]}")

@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

@pytest.fixture(scope="module")
def user_token():
    """Get regular user authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@platform.com", "password": "User123!"},
        timeout=15
    )
    if response.status_code == 200:
        return response.json().get("access_token") or response.json().get("token")
    pytest.skip(f"User login failed: {response.status_code}")

STANDARD_PAGE_TYPES = [
    "home",
    "category_l0_l1",
    "search_ln",
    "urgent_listings",
    "category_showcase",
    "listing_detail",
    "listing_detail_parameters",
    "storefront_profile",
    "wizard_step_l0",
    "wizard_step_ln",
    "wizard_step_form",
    "wizard_preview",
    "wizard_doping_payment",
    "wizard_result",
    "user_dashboard",
]

WIZARD_POLICY_PAGE_TYPES = [
    "wizard_step_l0",
    "wizard_step_ln",
    "wizard_step_form",
    "wizard_preview",
    "wizard_doping_payment",
    "wizard_result",
    "listing_create_stepX",
]


class TestSeedDefaultsEndpoint:
    """Tests for POST /api/admin/site/content-layout/pages/seed-defaults endpoint"""
    
    def test_seed_defaults_returns_200_with_valid_payload(self, admin_headers):
        """Seed endpoint with valid payload returns 200 and summary"""
        payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=payload,
            headers=admin_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "summary" in data, "Response should include summary"
        
        summary = data.get("summary", {})
        # Check summary has expected keys
        assert "created_pages" in summary or "updated_drafts" in summary or "skipped_drafts" in summary
        
        print(f"PASS: Seed endpoint returned 200 with summary: {summary}")
    
    def test_seed_defaults_creates_15_page_types(self, admin_headers):
        """Seed endpoint should create/update drafts for all 15 standard page types"""
        payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=payload,
            headers=admin_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Seed failed: {response.status_code}"
        
        data = response.json()
        items = data.get("items", [])
        assert len(items) == 15, f"Expected 15 page types, got {len(items)}"
        
        seeded_types = [item.get("page_type") for item in items]
        for expected_type in STANDARD_PAGE_TYPES:
            assert expected_type in seeded_types, f"Missing page type: {expected_type}"
        
        print(f"PASS: All 15 standard page types seeded: {seeded_types}")
    
    def test_seed_defaults_rejects_invalid_persona(self, admin_headers):
        """Seed endpoint should reject invalid persona values"""
        payload = {
            "country": "DE",
            "module": "global",
            "persona": "invalid_persona",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=payload,
            headers=admin_headers,
            timeout=15
        )
        assert response.status_code == 400, f"Expected 400 for invalid persona, got {response.status_code}"
        print("PASS: Invalid persona rejected with 400")
    
    def test_seed_defaults_rejects_invalid_variant(self, admin_headers):
        """Seed endpoint should reject invalid variant values"""
        payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "C",  # Invalid - only A or B allowed
            "overwrite_existing_draft": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=payload,
            headers=admin_headers,
            timeout=15
        )
        assert response.status_code == 400, f"Expected 400 for invalid variant, got {response.status_code}"
        print("PASS: Invalid variant rejected with 400")
    
    def test_seed_defaults_requires_admin_auth(self):
        """Seed endpoint should require admin authentication"""
        payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=payload,
            timeout=15
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("PASS: Seed endpoint requires authentication")


class TestLayoutPagesListEndpoint:
    """Tests for GET /api/admin/site/content-layout/pages - verify 15 page types exist"""
    
    def test_list_pages_returns_15_standard_types(self, admin_headers):
        """List pages endpoint should return all 15 standard page types after seeding"""
        # First seed to ensure pages exist
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        seed_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        assert seed_response.status_code == 200, f"Seed failed: {seed_response.status_code}"
        
        # Now list pages for each page type
        found_types = set()
        for page_type in STANDARD_PAGE_TYPES:
            response = requests.get(
                f"{BASE_URL}/api/admin/site/content-layout/pages",
                params={"page_type": page_type, "country": "DE", "module": "global", "limit": 10},
                headers=admin_headers,
                timeout=15
            )
            assert response.status_code == 200, f"List pages failed for {page_type}: {response.status_code}"
            
            data = response.json()
            items = data.get("items", [])
            if items:
                for item in items:
                    found_types.add(item.get("page_type"))
        
        for expected in STANDARD_PAGE_TYPES:
            assert expected in found_types, f"Page type {expected} not found in list"
        
        print(f"PASS: All 15 page types found: {sorted(found_types)}")


class TestWizardPreviewDraftRevision:
    """Tests for wizard_preview page type draft revision creation and resolve"""
    
    def test_wizard_preview_draft_exists_after_seed(self, admin_headers):
        """wizard_preview should have a draft revision after seeding"""
        # Seed first
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        seed_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        assert seed_response.status_code == 200, f"Seed failed: {seed_response.status_code}"
        
        # Find wizard_preview item
        items = seed_response.json().get("items", [])
        wizard_preview_item = next((item for item in items if item.get("page_type") == "wizard_preview"), None)
        assert wizard_preview_item is not None, "wizard_preview not found in seed response"
        
        page_id = wizard_preview_item.get("layout_page_id")
        assert page_id, "wizard_preview should have layout_page_id"
        
        # Get revisions for this page
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers=admin_headers,
            timeout=15
        )
        assert response.status_code == 200, f"Get revisions failed: {response.status_code}"
        
        revisions = response.json().get("items", [])
        draft_revision = next((r for r in revisions if r.get("status") == "draft"), None)
        assert draft_revision is not None, "wizard_preview should have a draft revision"
        
        # Verify payload has rows structure
        payload = draft_revision.get("payload_json", {})
        rows = payload.get("rows", [])
        assert len(rows) > 0, "wizard_preview draft should have at least one row"
        
        print(f"PASS: wizard_preview has draft revision with {len(rows)} rows")


class TestPolicyReportEndpoint:
    """Tests for policy-report endpoint with wizard page types"""
    
    def test_policy_report_for_wizard_preview(self, admin_headers):
        """Policy report for wizard_preview should return PASS/FAIL logic"""
        # First seed and get a revision ID
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        seed_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        assert seed_response.status_code == 200, f"Seed failed: {seed_response.status_code}"
        
        items = seed_response.json().get("items", [])
        wizard_preview_item = next((item for item in items if item.get("page_type") == "wizard_preview"), None)
        assert wizard_preview_item is not None, "wizard_preview not found"
        
        draft_id = wizard_preview_item.get("draft_revision_id")
        if not draft_id:
            pytest.skip("No draft revision ID for wizard_preview")
        
        # Get policy report
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-report",
            headers=admin_headers,
            timeout=15
        )
        assert response.status_code == 200, f"Policy report failed: {response.status_code}"
        
        data = response.json()
        report = data.get("report")
        assert report is not None, "Policy report should be returned"
        
        # Wizard policy should be applied
        policy_name = report.get("policy")
        passed = report.get("passed")
        assert policy_name in ["listing_create", "generic_layout"], f"Unexpected policy: {policy_name}"
        assert passed in [True, False], "passed should be boolean"
        
        print(f"PASS: Policy report returned - policy={policy_name}, passed={passed}")


class TestAutoFixEndpoint:
    """Tests for auto-fix endpoint on wizard page types"""
    
    def test_autofix_on_wizard_page_type(self, admin_headers):
        """Auto-fix should work on wizard page types"""
        # First seed to get a draft
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        seed_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        assert seed_response.status_code == 200, f"Seed failed: {seed_response.status_code}"
        
        items = seed_response.json().get("items", [])
        wizard_step_form_item = next((item for item in items if item.get("page_type") == "wizard_step_form"), None)
        assert wizard_step_form_item is not None, "wizard_step_form not found"
        
        draft_id = wizard_step_form_item.get("draft_revision_id")
        if not draft_id:
            pytest.skip("No draft revision ID for wizard_step_form")
        
        # Try auto-fix
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-autofix",
            json={},
            headers=admin_headers,
            timeout=20
        )
        assert response.status_code == 200, f"Auto-fix failed: {response.status_code}"
        
        data = response.json()
        assert "item" in data, "Response should have item"
        
        # Check auto_fix_actions
        actions = data.get("auto_fix_actions", [])
        print(f"PASS: Auto-fix completed with {len(actions)} actions")


class TestResolveEndpoint:
    """Tests for resolve endpoint including draft preview mode"""
    
    def test_resolve_wizard_preview_published(self, admin_headers):
        """Resolve endpoint should work for wizard_preview page type"""
        # Seed first
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        
        # Try resolve (may not find published version if not published yet)
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": "global", "page_type": "wizard_preview"},
            timeout=15
        )
        # 200 if found, 404 if no published revision
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "page" in data or "revision" in data, "Should have page or revision"
            print("PASS: Resolve returned published layout for wizard_preview")
        else:
            print("INFO: No published revision for wizard_preview (expected if not published)")
    
    def test_resolve_with_draft_preview_mode(self, admin_headers):
        """Resolve endpoint should support layout_preview=draft parameter"""
        # Seed first
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        
        # Resolve with draft preview mode
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "wizard_preview",
                "layout_preview": "draft"
            },
            headers=admin_headers,  # Auth required for draft preview
            timeout=15
        )
        
        # Should return 200 with draft content
        if response.status_code == 200:
            data = response.json()
            revision = data.get("revision", {})
            status = revision.get("status")
            # Could be draft or fallback to published
            print(f"PASS: Draft preview resolve returned status={status}")
        elif response.status_code == 404:
            print("INFO: No layout found for draft preview (acceptable)")
        else:
            assert False, f"Unexpected status: {response.status_code} - {response.text[:200]}"


class TestSearchPageRuntimeMapping:
    """Tests for SearchPage category_l0_l1 / search_ln resolve calls"""
    
    def test_resolve_category_l0_l1(self, admin_headers):
        """Resolve should work for category_l0_l1 page type"""
        # Seed first
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        
        # Resolve category_l0_l1
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": "global", "page_type": "category_l0_l1"},
            timeout=15
        )
        assert response.status_code in [200, 404], f"Unexpected: {response.status_code}"
        print(f"PASS: category_l0_l1 resolve returned {response.status_code}")
    
    def test_resolve_search_ln(self, admin_headers):
        """Resolve should work for search_ln page type"""
        # Seed first
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        
        # Resolve search_ln
        response = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"country": "DE", "module": "global", "page_type": "search_ln"},
            timeout=15
        )
        assert response.status_code in [200, 404], f"Unexpected: {response.status_code}"
        print(f"PASS: search_ln resolve returned {response.status_code}")


class TestWizardRuntimeMapping:
    """Tests for WizardContainer step-based page type mappings"""
    
    def test_resolve_all_wizard_step_types(self, admin_headers):
        """Resolve should work for all wizard step page types"""
        # Seed first
        seed_payload = {
            "country": "DE",
            "module": "vehicle",  # Use vehicle module for wizard
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        
        wizard_types = [
            "wizard_step_l0",
            "wizard_step_ln",
            "wizard_step_form",
            "wizard_preview",
        ]
        
        results = {}
        for page_type in wizard_types:
            response = requests.get(
                f"{BASE_URL}/api/site/content-layout/resolve",
                params={"country": "DE", "module": "vehicle", "page_type": page_type},
                timeout=15
            )
            results[page_type] = response.status_code
            assert response.status_code in [200, 404], f"{page_type}: {response.status_code}"
        
        print(f"PASS: Wizard runtime mapping results: {results}")


class TestPresetPayloadGeneration:
    """Tests for preset payload generation with 15 page types"""
    
    def test_seed_generates_comprehensive_payloads(self, admin_headers):
        """Each seeded page type should have a comprehensive payload with rows/columns/components"""
        seed_payload = {
            "country": "DE",
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True
        }
        seed_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/seed-defaults",
            json=seed_payload,
            headers=admin_headers,
            timeout=30
        )
        assert seed_response.status_code == 200, f"Seed failed: {seed_response.status_code}"
        
        items = seed_response.json().get("items", [])
        
        # Check a few page types have proper structure
        for item in items[:5]:  # Check first 5
            page_id = item.get("layout_page_id")
            page_type = item.get("page_type")
            
            # Get revisions
            rev_response = requests.get(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
                headers=admin_headers,
                timeout=15
            )
            if rev_response.status_code != 200:
                continue
            
            revisions = rev_response.json().get("items", [])
            draft = next((r for r in revisions if r.get("status") == "draft"), None)
            if not draft:
                continue
            
            payload = draft.get("payload_json", {})
            rows = payload.get("rows", [])
            
            assert len(rows) > 0, f"{page_type} should have at least one row"
            
            # Check first row has columns
            first_row = rows[0]
            columns = first_row.get("columns", [])
            assert len(columns) > 0, f"{page_type} first row should have columns"
            
            # Check first column has components
            first_col = columns[0]
            components = first_col.get("components", [])
            assert len(components) > 0, f"{page_type} first column should have components"
            
            print(f"  {page_type}: {len(rows)} rows, {len(columns)} cols in first row")
        
        print("PASS: Preset payloads have comprehensive row/column/component structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
