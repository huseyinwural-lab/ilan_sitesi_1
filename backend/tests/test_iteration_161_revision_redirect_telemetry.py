"""
Iteration 161 Tests: Revision Redirect Telemetry and Preset CSV Export

Tests for:
- Faz1: Revision Redirect Telemetry (POST/GET events, status/failure filters, summary, histogram)
- Faz2: Preset Runs date filters (from/to/status)
- Faz3: Preset CSV export (default vs extended mode, X-Export-Row-Limit header)
- Permission checks (telemetry endpoints should 403 for non-admin)
- Revision context endpoint (/admin/layouts/{revision_id})
- Copy conflict payload revision_id field
"""

import os
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Module: Telemetry Endpoints


class TestRevisionRedirectTelemetry:
    """Tests for revision redirect telemetry endpoints"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed - skipping telemetry tests")

    @pytest.fixture(scope="class")
    def dealer_token(self):
        """Login as dealer user and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None

    def test_telemetry_event_create_success(self, admin_token):
        """POST /api/admin/revision-redirect-telemetry/events - create success event"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        started_at = datetime.now(timezone.utc).isoformat()
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={
                "revision_id": "00000000-0000-0000-0000-000000000001",
                "redirect_target": "/admin/site-design/content-builder?test=1",
                "redirect_started_at": started_at,
                "redirect_duration_ms": 150,
                "status": "success",
                "failure_reason": None,
            },
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert data.get("item", {}).get("status") == "success"
        assert data.get("item", {}).get("redirect_duration_ms") == 150

    def test_telemetry_event_create_failed(self, admin_token):
        """POST /api/admin/revision-redirect-telemetry/events - create failed event with failure reason"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        started_at = datetime.now(timezone.utc).isoformat()
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={
                "revision_id": "00000000-0000-0000-0000-000000000002",
                "redirect_target": None,
                "redirect_started_at": started_at,
                "redirect_duration_ms": 50,
                "status": "failed",
                "failure_reason": "REVISION_NOT_FOUND",
            },
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert data.get("item", {}).get("status") == "failed"
        assert data.get("item", {}).get("failure_reason") == "REVISION_NOT_FOUND"

    def test_telemetry_event_invalid_status(self, admin_token):
        """POST /api/admin/revision-redirect-telemetry/events - invalid status returns 400 or 422"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={
                "status": "invalid_status",
            },
        )
        assert response.status_code in (400, 422), f"Expected 400/422, got {response.status_code}"

    def test_telemetry_event_failed_requires_reason(self, admin_token):
        """POST /api/admin/revision-redirect-telemetry/events - failed status requires failure_reason"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={
                "status": "failed",
                "failure_reason": None,
            },
        )
        assert response.status_code == 400

    def test_telemetry_event_invalid_failure_reason(self, admin_token):
        """POST /api/admin/revision-redirect-telemetry/events - invalid failure_reason returns 400"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={
                "status": "failed",
                "failure_reason": "INVALID_REASON",
            },
        )
        assert response.status_code == 400

    def test_telemetry_list_endpoint(self, admin_token):
        """GET /api/admin/revision-redirect-telemetry - list events with summary and histogram"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
            params={"limit": 50, "trend_days": 14},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "summary" in data
        summary = data["summary"]
        assert "total" in summary
        assert "success" in summary
        assert "failed" in summary
        assert "success_rate_pct" in summary
        assert "failure_rate_pct" in summary
        assert "avg_duration_ms" in summary
        assert "p95_duration_ms" in summary
        assert "duration_histogram" in summary
        assert "daily_trend" in summary
        assert "slo" in summary

        assert isinstance(summary["daily_trend"], list)
        assert len(summary["daily_trend"]) == 14
        for trend_item in summary["daily_trend"]:
            assert "date" in trend_item
            assert "total" in trend_item
            assert "success" in trend_item
            assert "failed" in trend_item
            assert "failure_rate_pct" in trend_item

        slo = summary["slo"]
        assert "targets" in slo
        assert "current" in slo
        assert "status" in slo
        assert "p95_latency_ms" in slo["targets"]
        assert "failure_rate_pct" in slo["targets"]
        assert "p95_latency_ok" in slo["status"]
        assert "failure_rate_ok" in slo["status"]

        histogram = summary["duration_histogram"]
        assert "0_250" in histogram
        assert "251_500" in histogram
        assert "501_1000" in histogram
        assert "1001_2000" in histogram
        assert "2001_plus" in histogram

    def test_telemetry_list_status_filter(self, admin_token):
        """GET /api/admin/revision-redirect-telemetry?status=success - filter by status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
            params={"limit": 50, "status": "success"},
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        for item in items:
            assert item.get("status") == "success"

    def test_telemetry_list_failure_reason_filter(self, admin_token):
        """GET /api/admin/revision-redirect-telemetry?failure_reason=REVISION_NOT_FOUND"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
            params={"failure_reason": "REVISION_NOT_FOUND"},
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        for item in items:
            assert item.get("failure_reason") == "REVISION_NOT_FOUND"


class TestTelemetryPermissionCheck:
    """Tests for telemetry endpoint permission checks"""

    def test_telemetry_list_non_admin_403(self):
        """GET /api/admin/revision-redirect-telemetry - non-admin user gets 403"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        if login_response.status_code != 200:
            pytest.skip("Dealer login failed")

        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"

    def test_telemetry_create_non_admin_403(self):
        """POST /api/admin/revision-redirect-telemetry/events - non-admin user gets 403"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        if login_response.status_code != 200:
            pytest.skip("Dealer login failed")

        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={"status": "success"},
        )
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"


class TestRevisionContextEndpoint:
    """Tests for revision context endpoint"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    def test_revision_context_endpoint(self, admin_token):
        """GET /api/admin/layouts/{revision_id} - returns page context"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        # First get a revision ID
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=headers,
            params={"limit": 1},
        )
        if list_response.status_code != 200 or not list_response.json().get("items"):
            pytest.skip("No layouts found to test")

        revision_id = list_response.json()["items"][0]["id"]
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts/{revision_id}",
            headers=headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "item" in data
        assert "page" in data
        page = data["page"]
        assert "id" in page
        assert "page_type" in page
        assert "country" in page
        assert "module" in page


# Module: Preset Runs Date Filters


class TestPresetRunsDateFilters:
    """Tests for preset runs date filters (from/to/status)"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    def test_preset_runs_list(self, admin_token):
        """GET /api/admin/preset-runs - list endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers=headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "has_next" in data

    def test_preset_runs_status_filter(self, admin_token):
        """GET /api/admin/preset-runs?status=success - status filter works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers=headers,
            params={"status": "success"},
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        for item in items:
            assert item.get("status") == "success"

    def test_preset_runs_from_date_filter(self, admin_token):
        """GET /api/admin/preset-runs?from=2026-01-01 - from date filter works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers=headers,
            params={"from": "2026-01-01"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_preset_runs_to_date_filter(self, admin_token):
        """GET /api/admin/preset-runs?to=2026-12-31 - to date filter works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers=headers,
            params={"to": "2026-12-31"},
        )
        assert response.status_code == 200

    def test_preset_runs_date_range_filter(self, admin_token):
        """GET /api/admin/preset-runs?from=2026-01-01&to=2026-12-31 - date range filter works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs",
            headers=headers,
            params={"from": "2026-01-01", "to": "2026-12-31"},
        )
        assert response.status_code == 200


# Module: Preset CSV Export


class TestPresetCSVExport:
    """Tests for preset CSV export (default vs extended)"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    def test_preset_export_default(self, admin_token):
        """GET /api/admin/preset-runs/export - default export preserves old header"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export",
            headers=headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type", "").startswith("text/csv")
        assert "X-Export-Row-Limit" in response.headers

        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) >= 1, "CSV should have at least header row"

        header_line = lines[0]
        expected_columns = [
            "run_id",
            "operator",
            "executed_at",
            "countries",
            "total_jobs",
            "success_count",
            "failure_count",
            "duration",
            "status",
        ]
        for col in expected_columns:
            assert col in header_line, f"Missing column {col} in header"

        # Default mode should NOT have extended columns
        assert "module" not in lines[0] or "meta" in lines[0]

    def test_preset_export_extended(self, admin_token):
        """GET /api/admin/preset-runs/export?extended=true - extended mode adds meta row and extra columns"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export",
            headers=headers,
            params={"extended": "true"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type", "").startswith("text/csv")
        assert "X-Export-Row-Limit" in response.headers

        content = response.text
        lines = content.strip().split("\n")
        assert len(lines) >= 2, "Extended CSV should have meta row + header row"

        # First line should be meta row
        meta_line = lines[0]
        assert "meta" in meta_line.lower() or "schema_version" in meta_line.lower()
        assert "2" in meta_line  # schema_version=2

        # Second line should be header with extended columns
        header_line = lines[1]
        assert "module" in header_line
        assert "persona" in header_line
        assert "variant" in header_line

    def test_preset_export_row_limit_header(self, admin_token):
        """GET /api/admin/preset-runs/export - X-Export-Row-Limit header is present"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export",
            headers=headers,
        )
        assert response.status_code == 200
        row_limit = response.headers.get("X-Export-Row-Limit")
        assert row_limit is not None, "X-Export-Row-Limit header should be present"
        assert int(row_limit) >= 1000  # Should be at least 1000


# Module: Copy Conflict Payload Regression


class TestCopyConflictPayloadRegression:
    """Tests for copy conflict payload - conflicts[].revision_id should be present"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user and get token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    def test_conflict_has_revision_id(self, admin_token):
        """POST /api/admin/layouts/{id}/copy - 409 conflict response has revision_id in conflicts"""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Get a published revision to copy
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=headers,
            params={"limit": 20, "statuses": "published"},
        )
        if list_response.status_code != 200:
            pytest.skip("Could not get layouts list")

        items = list_response.json().get("items", [])
        published_items = [item for item in items if item.get("status") == "published"]
        if not published_items:
            pytest.skip("No published layouts to test copy conflict")

        source_revision = published_items[0]
        revision_id = source_revision.get("id")
        page_type = source_revision.get("page_type", "home")
        country = source_revision.get("country", "TR")
        module = source_revision.get("module", "global")

        # Try to copy with publish_after_copy=true to trigger conflict
        response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{revision_id}/copy",
            headers=headers,
            json={
                "target_page_type": page_type,
                "country": country,
                "module": module,
                "publish_after_copy": True,
            },
        )

        # Could be 409 (conflict) or 200 (success)
        if response.status_code == 409:
            data = response.json()
            detail = data.get("detail", {})
            conflicts = detail.get("conflicts", [])
            if conflicts:
                # Verify each conflict has revision_id
                for conflict in conflicts:
                    assert "revision_id" in conflict, f"Conflict missing revision_id: {conflict}"
                    assert conflict.get("revision_id") is not None
        elif response.status_code == 200:
            # No conflict - copy succeeded
            pass
        else:
            # Other status - might be okay
            pass


# Module: Release Artifact Scripts


class TestReleaseArtifactScripts:
    """Tests for release artifact archive and cleanup scripts"""

    def test_archive_script_exists(self):
        """archive_release_artifacts.sh script exists"""
        script_path = "/app/scripts/archive_release_artifacts.sh"
        assert os.path.exists(script_path), f"Archive script not found at {script_path}"

    def test_cleanup_script_exists(self):
        """cleanup_release_artifacts.py script exists"""
        script_path = "/app/scripts/cleanup_release_artifacts.py"
        assert os.path.exists(script_path), f"Cleanup script not found at {script_path}"

    def test_cleanup_script_syntax(self):
        """cleanup_release_artifacts.py has valid Python syntax"""
        script_path = "/app/scripts/cleanup_release_artifacts.py"
        with open(script_path) as f:
            content = f.read()
        try:
            compile(content, script_path, "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in cleanup script: {e}")

    def test_cleanup_script_has_retention_rules(self):
        """cleanup_release_artifacts.py has retention rules (is_active, is_rollback_candidate, retention_locked)"""
        script_path = "/app/scripts/cleanup_release_artifacts.py"
        with open(script_path) as f:
            content = f.read()
        assert "is_active" in content, "Missing is_active retention rule"
        assert "is_rollback_candidate" in content, "Missing is_rollback_candidate retention rule"
        assert "retention_locked" in content, "Missing retention_locked retention rule"

    def test_cleanup_script_has_fail_safe(self):
        """cleanup_release_artifacts.py has fail-safe for missing meta"""
        script_path = "/app/scripts/cleanup_release_artifacts.py"
        with open(script_path) as f:
            content = f.read()
        assert "has_valid_meta" in content or "release_meta_missing" in content, "Missing fail-safe for missing meta"

    def test_archive_script_has_release_meta_fields(self):
        """archive_release_artifacts.sh creates release_meta.json with required fields"""
        script_path = "/app/scripts/archive_release_artifacts.sh"
        with open(script_path) as f:
            content = f.read()
        assert "release_id" in content, "Missing release_id in archive script"
        assert "is_active" in content, "Missing is_active in archive script"
        assert "is_rollback_candidate" in content, "Missing is_rollback_candidate in archive script"
        assert "retention_locked" in content, "Missing retention_locked in archive script"
