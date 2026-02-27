"""
P64 Publish hardening tests
- config_version mandatory for both publish endpoints
- conflict contract (409 CONFIG_VERSION_CONFLICT)
- publish lock race
- rollback reason mandatory
"""
import concurrent.futures
import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


def _admin_token() -> str:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"X-Portal-Scope": "admin"},
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text[:200]}")
    payload = response.json()
    return payload.get("access_token") or payload.get("token")


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _create_dashboard_draft(token: str, scope_id: str) -> tuple[str, int]:
    response = requests.post(
        f"{BASE_URL}/api/admin/ui/configs/dashboard",
        json={
            "segment": "corporate",
            "scope": "tenant",
            "scope_id": scope_id,
            "status": "draft",
            "config_data": {"title": "P64 Draft"},
            "layout": [
                {"widget_id": "kpi-1", "x": 0, "y": 0, "w": 3, "h": 1},
            ],
            "widgets": [
                {"widget_id": "kpi-1", "widget_type": "kpi", "title": "KPI", "enabled": True},
            ],
        },
        headers=_headers(token),
    )
    assert response.status_code == 200, f"Draft create failed: {response.text[:300]}"
    item = response.json().get("item") or {}
    return item.get("id"), item.get("version")


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _admin_token()


class TestPublishVersionContracts:
    def test_publish_new_endpoint_requires_config_version(self, admin_token: str):
        scope_id = f"p64-missing-new-{uuid.uuid4().hex[:8]}"
        _create_dashboard_draft(admin_token, scope_id)

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"
        detail = response.json().get("detail") or {}
        assert detail.get("code") == "MISSING_CONFIG_VERSION"

    def test_publish_legacy_endpoint_removed_returns_410(self, admin_token: str):
        scope_id = f"p64-missing-legacy-{uuid.uuid4().hex[:8]}"
        config_id, _ = _create_dashboard_draft(admin_token, scope_id)

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/{config_id}",
            json={},
            headers=_headers(admin_token),
        )
        assert response.status_code == 410, f"Expected 410, got {response.status_code}: {response.text[:300]}"
        detail = response.json().get("detail") or {}
        assert detail.get("code") == "LEGACY_ENDPOINT_REMOVED"

    def test_publish_version_mismatch_returns_409_contract(self, admin_token: str):
        scope_id = f"p64-conflict-{uuid.uuid4().hex[:8]}"
        config_id, version = _create_dashboard_draft(admin_token, scope_id)

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": config_id,
                "config_version": (version or 1) + 1,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text[:300]}"
        detail = response.json().get("detail") or {}
        assert detail.get("code") == "CONFIG_VERSION_CONFLICT"
        assert "current_version" in detail
        assert "your_version" in detail
        assert "last_published_by" in detail
        assert "last_published_at" in detail


class TestPublishLockAndRollbackReason:
    def test_parallel_publish_lock_or_conflict(self, admin_token: str):
        scope_id = f"p64-race-{uuid.uuid4().hex[:8]}"
        config_id, version = _create_dashboard_draft(admin_token, scope_id)

        payload = {
            "segment": "corporate",
            "scope": "tenant",
            "scope_id": scope_id,
            "config_id": config_id,
            "config_version": version,
            "require_confirm": True,
        }

        def _publish_once():
            return requests.post(
                f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
                json=payload,
                headers=_headers(admin_token),
                timeout=20,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_publish_once) for _ in range(2)]
            responses = [future.result() for future in futures]

        status_codes = sorted([response.status_code for response in responses])
        assert 200 in status_codes, f"Expected one success, got {status_codes}"
        assert 409 in status_codes, f"Expected one 409 conflict/lock, got {status_codes}"

        error_payloads = [
            response.json().get("detail")
            for response in responses
            if response.status_code == 409
        ]
        assert any(
            isinstance(detail, dict) and detail.get("code") in {"CONFIG_VERSION_CONFLICT", "PUBLISH_LOCKED"}
            for detail in error_payloads
        ), f"Expected conflict/lock code in 409 response: {error_payloads}"

    def test_rollback_reason_required(self, admin_token: str):
        scope_id = f"p64-rollback-reason-{uuid.uuid4().hex[:8]}"
        config_id, version = _create_dashboard_draft(admin_token, scope_id)

        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": config_id,
                "config_version": version,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert publish_response.status_code == 200, f"Publish failed: {publish_response.text[:300]}"

        rollback_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/rollback",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert rollback_response.status_code == 400, f"Expected 400, got {rollback_response.status_code}: {rollback_response.text[:300]}"
        detail = rollback_response.json().get("detail") or {}
        assert detail.get("code") == "MISSING_ROLLBACK_REASON"
