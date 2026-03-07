"""
Iteration 167 Tests
- Faz 2: release retention dry-run + execute confirm + audit logs
- Faz 3: integrity scan report
- Faz 4: async CSV export jobs + cancel/download + dealer scoped export
- Faz 6 RBAC: dealer/user /admin/* erişimi
"""

import os
import time

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _login(email: str, password: str):
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        return None
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    token = _login("admin@platform.com", "Admin123!")
    if not token:
        pytest.skip("admin login failed")
    return token


@pytest.fixture(scope="module")
def dealer_token():
    token = _login("dealer@platform.com", "Dealer123!")
    if not token:
        pytest.skip("dealer login failed")
    return token


@pytest.fixture(scope="module")
def user_token():
    token = _login("user@platform.com", "User123!")
    if not token:
        pytest.skip("user login failed")
    return token


def _headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


class TestReleaseRetention:
    def test_dry_run_works_for_admin(self, admin_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/release-retention/dry-run",
            headers=_headers(admin_token),
            params={"retention_window_days": 21},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        dry_run = payload.get("dry_run") or {}
        assert "total_artifacts" in dry_run
        assert "protected_count" in dry_run
        assert "delete_candidates_count" in dry_run
        assert isinstance(dry_run.get("keep"), list)
        assert isinstance(dry_run.get("delete"), list)

    def test_execute_requires_confirmation(self, admin_token):
        response = requests.post(
            f"{BASE_URL}/api/admin/release-retention/execute",
            headers=_headers(admin_token),
            json={
                "retention_window_days": 3650,
                "expected_delete_count": 0,
                "confirm": False,
                "trigger_source": "test_suite",
            },
            timeout=30,
        )
        assert response.status_code == 400, response.text

    def test_execute_cleanup_with_safe_window(self, admin_token):
        response = requests.post(
            f"{BASE_URL}/api/admin/release-retention/execute",
            headers=_headers(admin_token),
            json={
                "retention_window_days": 3650,
                "expected_delete_count": 0,
                "confirm": True,
                "trigger_source": "test_suite",
            },
            timeout=60,
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload.get("ok") is True
        assert payload.get("deleted_count") == 0
        assert "audit" in payload

    def test_audit_logs_visible(self, admin_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/release-retention/audit-logs",
            headers=_headers(admin_token),
            params={"page": 1, "limit": 10},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert isinstance(payload.get("items"), list)

    def test_integrity_scan_report(self, admin_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/release-retention/integrity-scan",
            headers=_headers(admin_token),
            params={"write_report": "true"},
            timeout=60,
        )
        assert response.status_code == 200, response.text
        report = (response.json() or {}).get("report") or {}
        summary = report.get("summary") or {}
        assert "valid_artifacts" in summary
        assert "missing_metadata" in summary
        assert "corrupted_artifacts" in summary
        report_path = report.get("report_path")
        assert report_path and os.path.exists(report_path), f"report file missing: {report_path}"


class TestPresetExportJobs:
    def _wait_final_status(self, token: str, job_id: str):
        for _ in range(20):
            response = requests.get(
                f"{BASE_URL}/api/admin/preset-runs/export-jobs/{job_id}",
                headers=_headers(token),
                timeout=20,
            )
            assert response.status_code == 200, response.text
            status = (response.json().get("item") or {}).get("status")
            if status in {"completed", "failed", "cancelled"}:
                return status
            time.sleep(1)
        return None

    def test_admin_create_list_and_download_job(self, admin_token):
        create_response = requests.post(
            f"{BASE_URL}/api/admin/preset-runs/export-jobs",
            headers=_headers(admin_token),
            json={
                "status": "success",
                "extended": True,
            },
            timeout=30,
        )
        assert create_response.status_code == 200, create_response.text
        item = (create_response.json() or {}).get("item") or {}
        job_id = item.get("job_id")
        assert job_id, f"job_id missing: {create_response.text}"

        list_response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export-jobs",
            headers=_headers(admin_token),
            timeout=30,
        )
        assert list_response.status_code == 200, list_response.text
        list_items = list_response.json().get("items") or []
        assert any(x.get("job_id") == job_id for x in list_items), "created job not in list"

        final_status = self._wait_final_status(admin_token, job_id)
        assert final_status in {"completed", "failed", "cancelled"}
        if final_status == "completed":
            download_response = requests.get(
                f"{BASE_URL}/api/admin/preset-runs/export-jobs/{job_id}/download",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=30,
            )
            assert download_response.status_code == 200, download_response.text[:200]
            assert "text/csv" in str(download_response.headers.get("content-type", ""))

    def test_admin_cancel_running_or_queued_job(self, admin_token):
        create_response = requests.post(
            f"{BASE_URL}/api/admin/preset-runs/export-jobs",
            headers=_headers(admin_token),
            json={"status": "success"},
            timeout=30,
        )
        assert create_response.status_code == 200
        job_id = ((create_response.json() or {}).get("item") or {}).get("job_id")
        assert job_id

        cancel_response = requests.post(
            f"{BASE_URL}/api/admin/preset-runs/export-jobs/{job_id}/cancel",
            headers=_headers(admin_token),
            timeout=30,
        )
        assert cancel_response.status_code == 200, cancel_response.text
        status = ((cancel_response.json() or {}).get("item") or {}).get("status")
        assert status in {"queued", "running", "cancelled", "completed", "failed"}

    def test_dealer_scoped_export(self, dealer_token):
        response = requests.post(
            f"{BASE_URL}/api/dealer/preset-runs/export-jobs",
            headers=_headers(dealer_token),
            json={"module": "global"},
            timeout=30,
        )
        assert response.status_code == 200, response.text
        item = (response.json().get("item") or {})
        assert item.get("export_scope") == "dealer"
        assert item.get("job_id")


class TestRBAC:
    def test_dealer_cannot_access_admin_export_jobs(self, dealer_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/preset-runs/export-jobs",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=20,
        )
        assert response.status_code == 403, response.text

    def test_dealer_cannot_execute_cleanup(self, dealer_token):
        response = requests.post(
            f"{BASE_URL}/api/admin/release-retention/execute",
            headers=_headers(dealer_token),
            json={
                "retention_window_days": 21,
                "confirm": True,
                "expected_delete_count": 0,
                "trigger_source": "test_suite",
            },
            timeout=20,
        )
        assert response.status_code == 403, response.text

    def test_dealer_cannot_access_telemetry_admin_endpoint(self, dealer_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=20,
        )
        assert response.status_code == 403, response.text

    def test_user_cannot_create_dealer_export_job(self, user_token):
        response = requests.post(
            f"{BASE_URL}/api/dealer/preset-runs/export-jobs",
            headers=_headers(user_token),
            json={"module": "global"},
            timeout=20,
        )
        assert response.status_code == 403, response.text
