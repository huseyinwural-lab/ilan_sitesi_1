"""
P66 Conflict UX + deterministic publish telemetry tests
"""
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


def _headers(token: str):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _create_dashboard_draft(token: str, scope_id: str, title: str = "Draft"):
    response = requests.post(
        f"{BASE_URL}/api/admin/ui/configs/dashboard",
        json={
            "segment": "corporate",
            "scope": "tenant",
            "scope_id": scope_id,
            "status": "draft",
            "config_data": {"title": title},
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
    return item


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _admin_token()


class TestConflictSyncAndTelemetry:
    def test_conflict_sync_endpoint_returns_latest_and_diff(self, admin_token: str):
        scope_id = f"p66-sync-{uuid.uuid4().hex[:8]}"
        first = _create_dashboard_draft(admin_token, scope_id, title="Draft v1")
        second = _create_dashboard_draft(admin_token, scope_id, title="Draft v2")

        sync_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/conflict-sync",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "previous_version": first.get("version"),
                "retry_count": 1,
            },
            headers=_headers(admin_token),
        )
        assert sync_response.status_code == 200, f"Conflict sync failed: {sync_response.text[:300]}"
        payload = sync_response.json()
        assert payload.get("item", {}).get("version") == second.get("version")
        assert isinstance(payload.get("items"), list)
        assert payload.get("diff", {}).get("config_type") == "dashboard"

    def test_publish_telemetry_endpoint_and_hash_guard(self, admin_token: str):
        scope_id = f"p66-telemetry-{uuid.uuid4().hex[:8]}"
        draft = _create_dashboard_draft(admin_token, scope_id, title="Telemetry Draft")
        config_id = draft.get("id")
        version = draft.get("version")

        hash_mismatch = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": config_id,
                "config_version": version,
                "resolved_config_hash": "bad-hash",
                "retry_count": 2,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert hash_mismatch.status_code == 409
        assert (hash_mismatch.json().get("detail") or {}).get("code") == "CONFIG_HASH_MISMATCH"

        publish_ok = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": config_id,
                "config_version": version,
                "resolved_config_hash": draft.get("resolved_config_hash"),
                "retry_count": 3,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert publish_ok.status_code == 200, f"Publish failed: {publish_ok.text[:300]}"

        telemetry_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish-audits?segment=corporate&scope=tenant&scope_id={scope_id}&limit=20",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert telemetry_response.status_code == 200, f"Telemetry endpoint failed: {telemetry_response.text[:300]}"
        telemetry_payload = telemetry_response.json()
        assert isinstance(telemetry_payload.get("items"), list)
        assert len(telemetry_payload.get("items") or []) >= 2
        metrics = telemetry_payload.get("telemetry") or {}
        assert "avg_lock_wait_ms" in metrics
        assert "max_lock_wait_ms" in metrics
        assert "publish_duration_ms" in metrics
        assert "publish_duration_ms_p95" in metrics

    def test_ops_thresholds_and_alert_simulation(self, admin_token: str):
        thresholds_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-thresholds",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert thresholds_response.status_code == 200
        thresholds = thresholds_response.json().get("thresholds") or {}
        assert "max_lock_wait_ms" in thresholds
        assert "conflict_rate" in thresholds

        simulation_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 300,
                "max_lock_wait_ms": 520,
                "publish_duration_ms_p95": 1800,
                "conflict_rate": 45,
            },
            headers=_headers(admin_token),
        )
        assert simulation_response.status_code == 200
        alerts = simulation_response.json().get("alerts") or []
        assert any(alert.get("metric") == "max_lock_wait_ms" and alert.get("severity") == "critical" for alert in alerts)

    def test_legacy_publish_returns_410_and_usage_visible(self, admin_token: str):
        scope_id = f"p66-legacy-{uuid.uuid4().hex[:8]}"
        draft = _create_dashboard_draft(admin_token, scope_id, title="Legacy call")
        config_id = draft.get("id")

        legacy_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/{config_id}",
            json={"config_version": draft.get("version")},
            headers=_headers(admin_token),
        )
        assert legacy_response.status_code == 410
        detail = legacy_response.json().get("detail") or {}
        assert detail.get("code") == "LEGACY_ENDPOINT_REMOVED"

        usage_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/legacy-usage?days=30",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert usage_response.status_code == 200
        usage_payload = usage_response.json()
        assert usage_payload.get("days") == 30
        assert usage_payload.get("total_calls", 0) >= 1
