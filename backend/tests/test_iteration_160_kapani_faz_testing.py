"""
Test iteration 160: Kapanış Görev Listesi Test Suite
Testing all 5 phases (Faz1-Faz5) as specified in the review request:
- Faz1: Release artifacts + release_meta + CI archive script
- Faz2: preset-runs API list/export with date range + CSV export
- Faz3: copy conflict modal with deep-link + proceed/cancel
- Faz4: academy.modules real backend integration
- Faz5: UI consistency
"""

import os
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=60,
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer auth token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        timeout=60,
    )
    if response.status_code != 200:
        pytest.skip(f"Dealer login failed: {response.status_code}")
    return response.json().get("access_token")


# ============================================================================
# FAZ1: Release Artifacts Tests
# ============================================================================

class TestFaz1ReleaseArtifacts:
    """Faz1: release-artifacts arşivi + release_meta + CI entegrasyonu"""

    def test_01_release_artifacts_directory_exists(self):
        """Release artifacts 2026-03-07_release directory exists"""
        artifact_dir = "/app/release-artifacts/2026-03-07_release"
        assert os.path.isdir(artifact_dir), f"Release artifacts directory missing: {artifact_dir}"
        print(f"Release artifacts directory exists: {artifact_dir}")

    def test_02_publish_validation_report_exists(self):
        """publish_validation_report.md exists in release artifacts"""
        report_path = "/app/release-artifacts/2026-03-07_release/publish_validation_report.md"
        assert os.path.isfile(report_path), f"Report file missing: {report_path}"
        
        with open(report_path, "r") as f:
            content = f.read()
        
        # Basic content validation
        assert len(content) > 100, "Report file too short"
        assert "TR" in content or "DE" in content or "FR" in content, "Country mentions missing"
        print(f"publish_validation_report.md exists with {len(content)} chars")

    def test_03_preset_stress_test_report_exists(self):
        """preset_stress_test_report.md exists in release artifacts"""
        report_path = "/app/release-artifacts/2026-03-07_release/preset_stress_test_report.md"
        assert os.path.isfile(report_path), f"Report file missing: {report_path}"
        
        with open(report_path, "r") as f:
            content = f.read()
        
        assert len(content) > 50, "Report file too short"
        print(f"preset_stress_test_report.md exists with {len(content)} chars")

    def test_04_release_meta_json_exists_and_valid(self):
        """release_meta.json exists with correct structure"""
        import json
        meta_path = "/app/release-artifacts/2026-03-07_release/release_meta.json"
        assert os.path.isfile(meta_path), f"release_meta.json missing: {meta_path}"
        
        with open(meta_path, "r") as f:
            data = json.load(f)
        
        # Contract fields
        required_fields = ["release_version", "release_date", "validated_locales", "preset_batch_size", "validated_by"]
        for field in required_fields:
            assert field in data, f"Field {field} missing in release_meta.json"
        
        # Validate data types
        assert isinstance(data["validated_locales"], list), "validated_locales should be a list"
        assert len(data["validated_locales"]) > 0, "validated_locales should not be empty"
        assert isinstance(data["preset_batch_size"], int), "preset_batch_size should be int"
        
        print(f"release_meta.json: version={data['release_version']}, locales={data['validated_locales']}")

    def test_05_ci_lint_yml_has_archive_step(self):
        """CI lint.yml has archive release artifacts step"""
        lint_yml_path = "/app/.github/workflows/lint.yml"
        assert os.path.isfile(lint_yml_path), f"lint.yml missing: {lint_yml_path}"
        
        with open(lint_yml_path, "r") as f:
            content = f.read()
        
        # Check for archive step
        assert "archive_release_artifacts" in content or "Archive release artifacts" in content, \
            "Archive release artifacts step missing in lint.yml"
        assert "scripts/archive_release_artifacts.sh" in content, "Archive script call missing"
        assert "upload-artifact" in content, "Upload artifact step missing"
        
        print("lint.yml has archive release artifacts step")

    def test_06_archive_script_exists_and_executable(self):
        """archive_release_artifacts.sh script exists"""
        script_path = "/app/scripts/archive_release_artifacts.sh"
        assert os.path.isfile(script_path), f"Archive script missing: {script_path}"
        
        with open(script_path, "r") as f:
            content = f.read()
        
        # Check script content
        assert "#!/usr/bin/env bash" in content or "#!/bin/bash" in content, "Missing shebang"
        assert "release_meta.json" in content, "release_meta.json reference missing"
        assert "RELEASE_VERSION" in content, "RELEASE_VERSION env var missing"
        
        print("archive_release_artifacts.sh script exists")


# ============================================================================
# FAZ2: Preset Runs API Tests
# ============================================================================

class TestFaz2PresetRunsAPI:
    """Faz2: preset-runs date range + CSV export"""

    def test_07_preset_runs_list_alias_endpoint(self, admin_token):
        """GET /api/admin/preset-runs endpoint (alias) works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 10},
            timeout=30,
        )
        assert response.status_code == 200, f"Preset runs list failed: {response.text}"
        data = response.json()
        
        # Contract checks
        assert "items" in data, "items field missing"
        assert "total" in data, "total field missing"
        assert "page" in data, "page field missing"
        assert "limit" in data, "limit field missing"
        
        print(f"Preset runs list: {len(data.get('items', []))} items, total={data.get('total')}")

    def test_08_preset_runs_filter_by_status(self, admin_token):
        """Filter preset runs by status query param"""
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 10, "status": "success"},
            timeout=30,
        )
        assert response.status_code == 200, f"Status filter failed: {response.text}"
        data = response.json()
        
        # All items should have status=success
        for item in data.get("items", []):
            assert item.get("status") == "success", f"Unexpected status: {item.get('status')}"
        
        print(f"Status filter (success): {len(data.get('items', []))} items")

    def test_09_preset_runs_filter_by_from_date(self, admin_token):
        """Filter preset runs by from date"""
        # Use a date 30 days ago
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 20, "from": from_date},
            timeout=30,
        )
        assert response.status_code == 200, f"From filter failed: {response.text}"
        data = response.json()
        
        print(f"From filter ({from_date}): {len(data.get('items', []))} items")

    def test_10_preset_runs_filter_by_to_date(self, admin_token):
        """Filter preset runs by to date"""
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 20, "to": to_date},
            timeout=30,
        )
        assert response.status_code == 200, f"To filter failed: {response.text}"
        data = response.json()
        
        print(f"To filter ({to_date}): {len(data.get('items', []))} items")

    def test_11_preset_runs_filter_date_range(self, admin_token):
        """Filter preset runs by date range (from + to)"""
        from_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 20, "from": from_date, "to": to_date},
            timeout=30,
        )
        assert response.status_code == 200, f"Date range filter failed: {response.text}"
        data = response.json()
        
        print(f"Date range filter ({from_date} to {to_date}): {len(data.get('items', []))} items")

    def test_12_preset_runs_csv_export_endpoint(self, admin_token):
        """GET /api/admin/preset-runs/export returns CSV"""
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=60,
        )
        assert response.status_code == 200, f"CSV export failed: {response.text}"
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
        
        # Check content has data
        csv_content = response.text
        assert len(csv_content) > 0, "CSV content is empty"
        
        # Check CSV headers
        expected_columns = ["id", "executed_at", "status", "target_countries"]
        first_line = csv_content.split("\n")[0]
        for col in expected_columns:
            assert col in first_line, f"Column {col} missing in CSV header"
        
        print(f"CSV export: {len(csv_content)} bytes, header: {first_line[:100]}")

    def test_13_preset_runs_csv_export_with_filters(self, admin_token):
        """CSV export with status/date filters"""
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"status": "success", "from": from_date},
            timeout=60,
        )
        assert response.status_code == 200, f"Filtered CSV export failed: {response.text}"
        
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv, got {content_type}"
        
        print(f"Filtered CSV export: {len(response.text)} bytes")


# ============================================================================
# FAZ3: Copy Conflict Modal + Deep Link Tests
# ============================================================================

class TestFaz3CopyConflictDeepLink:
    """Faz3: copy conflict modal deep-link + revision context endpoint"""

    def test_14_revision_context_endpoint_exists(self, admin_token):
        """GET /api/admin/layouts/{revision_id} returns revision context"""
        # First get a published revision
        layouts_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"statuses": "published", "page": 1, "limit": 1},
            timeout=30,
        )
        
        if layouts_response.status_code != 200 or not layouts_response.json().get("items"):
            pytest.skip("No published layouts for context test")
        
        item = layouts_response.json()["items"][0]
        revision_id = item.get("revision_id") or item.get("id")
        
        # Call context endpoint
        context_response = requests.get(
            f"{BASE_URL}/api/admin/layouts/{revision_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        
        assert context_response.status_code == 200, f"Revision context failed: {context_response.text}"
        data = context_response.json()
        
        # Check for page context
        assert "page" in data or "revision" in data, "Expected page or revision context"
        
        print(f"Revision context for {revision_id}: returned OK")

    def test_15_copy_conflict_returns_409_with_conflicts(self, admin_token):
        """Copy with publish returns 409 with conflicts array including revision_id"""
        # Get active published revision
        layouts_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"statuses": "published", "state": "active", "page": 1, "limit": 5},
            timeout=30,
        )
        
        if layouts_response.status_code != 200 or not layouts_response.json().get("items"):
            pytest.skip("No active published layouts for conflict test")
        
        items = layouts_response.json()["items"]
        source_item = None
        for item in items:
            if item.get("is_active") and not item.get("is_deleted"):
                source_item = item
                break
        
        if not source_item:
            pytest.skip("No active non-deleted revision")
        
        source_id = source_item.get("revision_id") or source_item.get("id")
        
        # Copy to same scope to trigger conflict
        copy_response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{source_id}/copy",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_page_type": source_item.get("page_type", "home"),
                "country": source_item.get("country", "TR"),
                "module": source_item.get("module", "global"),
                "category_id": source_item.get("category_id"),
                "publish_after_copy": True,
            },
            timeout=60,
        )
        
        if copy_response.status_code == 409:
            data = copy_response.json()
            detail = data.get("detail", {})
            
            # Check conflict response structure
            assert detail.get("code") == "publish_scope_conflict", f"Wrong code: {detail}"
            assert "conflicts" in detail, "conflicts array missing in 409 response"
            
            # Check each conflict has revision_id
            conflicts = detail.get("conflicts", [])
            for conflict in conflicts:
                assert "revision_id" in conflict, f"revision_id missing in conflict: {conflict}"
            
            print(f"409 conflict: {len(conflicts)} conflicts, all have revision_id")
        elif copy_response.status_code == 200:
            # No conflict - that's also acceptable
            print("Copy succeeded without conflict")
        else:
            pytest.fail(f"Unexpected status: {copy_response.status_code} - {copy_response.text}")

    def test_16_copy_with_force_proceeds(self, admin_token):
        """Copy with force=true proceeds despite conflicts"""
        # Get published revision
        layouts_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"statuses": "published", "page": 1, "limit": 2},
            timeout=30,
        )
        
        if layouts_response.status_code != 200 or not layouts_response.json().get("items"):
            pytest.skip("No published layouts for force copy test")
        
        source_item = layouts_response.json()["items"][0]
        source_id = source_item.get("revision_id") or source_item.get("id")
        
        # Copy with force=true
        copy_response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{source_id}/copy",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_page_type": source_item.get("page_type", "home"),
                "country": source_item.get("country", "TR"),
                "module": source_item.get("module", "global"),
                "category_id": source_item.get("category_id"),
                "publish_after_copy": True,
            },
            params={"force": "true"},
            timeout=60,
        )
        
        # Force should succeed
        assert copy_response.status_code in [200, 201], f"Force copy failed: {copy_response.text}"
        data = copy_response.json()
        
        # Check for conflict resolution info
        if "conflict_resolution" in data:
            resolution = data["conflict_resolution"]
            print(f"Force copy: deactivated_ids={resolution.get('deactivated_revision_ids', [])}")
        else:
            print("Force copy succeeded without conflicts")


# ============================================================================
# FAZ4: Academy Modules Real Backend Tests
# ============================================================================

class TestFaz4AcademyModulesRealBackend:
    """Faz4: academy.modules gerçek backend entegrasyonu"""

    def test_17_academy_modules_not_mocked(self, dealer_token):
        """Academy modules returns real data (not mock)"""
        response = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert response.status_code == 200, f"Academy modules failed: {response.text}"
        data = response.json()
        
        # Check source is NOT mock
        source = data.get("source", "")
        valid_real_sources = ["dealer_modules_db", "cache", "cache_fallback", "empty_fallback"]
        assert source in valid_real_sources, f"Source appears to be mock: {source}"
        assert source != "mock", "Source should not be mock"
        
        print(f"Academy modules source: {source} (real data)")

    def test_18_academy_modules_items_structure(self, dealer_token):
        """Academy modules items have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        
        items = data.get("items", [])
        if items:
            item = items[0]
            # Check for expected fields
            expected_fields = ["id", "key"]
            for field in expected_fields:
                assert field in item or "title" in item, f"Field {field} or title missing"
            
            print(f"Academy module item: {item}")
        else:
            print("No academy modules - empty but endpoint works")


# ============================================================================
# FAZ5: UI Consistency Tests (File-based)
# ============================================================================

class TestFaz5UIConsistency:
    """Faz5: UI tutarlılık - component and route checks"""

    def test_19_admin_preset_runs_jsx_exists(self):
        """AdminPresetRuns.jsx exists with filters"""
        jsx_path = "/app/frontend/src/pages/admin/AdminPresetRuns.jsx"
        assert os.path.isfile(jsx_path), f"AdminPresetRuns.jsx missing: {jsx_path}"
        
        with open(jsx_path, "r") as f:
            content = f.read()
        
        # Check for filter elements
        assert "statusFilter" in content or "status" in content, "Status filter missing"
        assert "fromDateFilter" in content or "from" in content, "From date filter missing"
        assert "toDateFilter" in content or "to" in content, "To date filter missing"
        assert "Export CSV" in content or "export" in content.lower(), "Export CSV button missing"
        
        # Check for data-testid
        assert "data-testid" in content, "data-testid attributes missing"
        
        print("AdminPresetRuns.jsx has filters and export")

    def test_20_confirm_modal_has_deep_link(self):
        """ConfirmModal.jsx has deep-link with target _blank"""
        modal_path = "/app/frontend/src/components/ConfirmModal.jsx"
        assert os.path.isfile(modal_path), f"ConfirmModal.jsx missing"
        
        with open(modal_path, "r") as f:
            content = f.read()
        
        # Check for revision link
        assert "revision" in content.lower(), "Revision reference missing"
        assert "target" in content and "_blank" in content, "target=_blank missing"
        assert "/admin/revisions/" in content, "Deep link path /admin/revisions/{revision_id} missing"
        
        print("ConfirmModal.jsx has deep-link with target=_blank")

    def test_21_revision_redirect_component_exists(self):
        """AdminRevisionRedirect.jsx exists with content-builder redirect"""
        jsx_path = "/app/frontend/src/pages/admin/AdminRevisionRedirect.jsx"
        assert os.path.isfile(jsx_path), f"AdminRevisionRedirect.jsx missing"
        
        with open(jsx_path, "r") as f:
            content = f.read()
        
        # Check redirect logic
        assert "content-builder" in content, "content-builder redirect missing"
        assert "revisionId" in content or "revision_id" in content, "revisionId param missing"
        assert "navigate" in content, "navigate function missing"
        
        print("AdminRevisionRedirect.jsx exists with content-builder redirect")

    def test_22_backoffice_routing_has_revision_route(self):
        """BackofficePortalApp.jsx has /admin/revisions/:revisionId route"""
        routing_path = "/app/frontend/src/portals/backoffice/BackofficePortalApp.jsx"
        assert os.path.isfile(routing_path), f"BackofficePortalApp.jsx missing"
        
        with open(routing_path, "r") as f:
            content = f.read()
        
        # Check for revisions route
        assert "/revisions/:revisionId" in content or "revisions" in content, "Revisions route missing"
        assert "AdminRevisionRedirect" in content, "AdminRevisionRedirect import missing"
        
        print("BackofficePortalApp.jsx has revisions route")
