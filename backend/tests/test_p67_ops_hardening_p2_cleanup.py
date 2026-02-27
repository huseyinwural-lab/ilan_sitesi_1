"""
P67 Operasyonel Stabilizasyon + P2 Cleanup Tests
- Legacy publish endpoint: 410 LEGACY_ENDPOINT_REMOVED + deprecation headers
- New publish endpoint flow with config_version+hash guard+scope checks
- Ops threshold endpoint: GET /api/admin/ui/configs/{config_type}/ops-thresholds
- Ops alert simulation: POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate
- Legacy usage analysis: GET /api/admin/ui/configs/{config_type}/legacy-usage?days=30
- Publish audits endpoint: KPI + telemetry + windows(1h/24h/7d) + trends
- Conflict sync endpoint: latest draft + diff
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


class TestLegacyPublishEndpoint410:
    """Legacy publish endpoint -> 410 LEGACY_ENDPOINT_REMOVED + deprecation headers"""

    def test_legacy_publish_returns_410_with_deprecation_code(self, admin_token: str):
        scope_id = f"p67-legacy-410-{uuid.uuid4().hex[:8]}"
        draft = _create_dashboard_draft(admin_token, scope_id, title="Legacy 410 test")
        config_id = draft.get("id")

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/{config_id}",
            json={"config_version": draft.get("version")},
            headers=_headers(admin_token),
        )
        
        # Verify 410 status code
        assert response.status_code == 410, f"Expected 410, got {response.status_code}: {response.text[:300]}"
        
        # Verify error code
        detail = response.json().get("detail") or {}
        assert detail.get("code") == "LEGACY_ENDPOINT_REMOVED", f"Expected LEGACY_ENDPOINT_REMOVED, got: {detail}"
        
        # Verify deprecation headers
        assert "Deprecation" in response.headers or "deprecation" in response.headers.keys(), "Missing Deprecation header"
        
    def test_legacy_usage_tracking_endpoint(self, admin_token: str):
        """GET /api/admin/ui/configs/{config_type}/legacy-usage?days=30"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/legacy-usage?days=30",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Legacy usage endpoint failed: {response.text[:300]}"
        
        payload = response.json()
        assert payload.get("days") == 30
        assert "total_calls" in payload
        assert isinstance(payload.get("client_breakdown"), list)


class TestNewPublishEndpointFlow:
    """New publish endpoint with config_version + hash guard + scope checks"""

    def test_publish_requires_config_version(self, admin_token: str):
        scope_id = f"p67-version-{uuid.uuid4().hex[:8]}"
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

    def test_publish_hash_mismatch_returns_409(self, admin_token: str):
        scope_id = f"p67-hash-{uuid.uuid4().hex[:8]}"
        draft = _create_dashboard_draft(admin_token, scope_id, title="Hash test")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": draft.get("id"),
                "config_version": draft.get("version"),
                "resolved_config_hash": "invalid-hash-value",
                "owner_type": "dealer",
                "owner_id": scope_id,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text[:300]}"
        detail = response.json().get("detail") or {}
        assert detail.get("code") == "CONFIG_HASH_MISMATCH"
        assert "current_hash" in detail
        assert "your_hash" in detail

    def test_publish_successful_with_correct_parameters(self, admin_token: str):
        scope_id = f"p67-success-{uuid.uuid4().hex[:8]}"
        draft = _create_dashboard_draft(admin_token, scope_id, title="Success test")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": draft.get("id"),
                "config_version": draft.get("version"),
                "resolved_config_hash": draft.get("resolved_config_hash"),
                "owner_type": "dealer",
                "owner_id": scope_id,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert data.get("item", {}).get("status") == "published"


class TestOpsThresholdEndpoint:
    """GET /api/admin/ui/configs/{config_type}/ops-thresholds"""

    def test_ops_thresholds_returns_valid_structure(self, admin_token: str):
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-thresholds",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Ops thresholds failed: {response.text[:300]}"
        
        payload = response.json()
        thresholds = payload.get("thresholds") or {}
        
        # Verify threshold structure
        assert "avg_lock_wait_ms" in thresholds
        assert "max_lock_wait_ms" in thresholds
        assert "publish_duration_ms_p95" in thresholds
        assert "conflict_rate" in thresholds
        
        # Verify escalation structure
        escalation = payload.get("escalation") or {}
        assert "warning" in escalation
        assert "critical" in escalation


class TestOpsAlertSimulation:
    """POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate"""

    def test_simulate_high_lock_wait_triggers_critical_alert(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 300,
                "max_lock_wait_ms": 520,
                "publish_duration_ms_p95": 1800,
                "conflict_rate": 45,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200, f"Alert simulation failed: {response.text[:300]}"
        
        alerts = response.json().get("alerts") or []
        
        # Verify critical alert for max_lock_wait_ms (>450 threshold)
        critical_lock_alert = next(
            (alert for alert in alerts 
             if alert.get("metric") == "max_lock_wait_ms" and alert.get("severity") == "critical"),
            None
        )
        assert critical_lock_alert is not None, f"Expected critical alert for max_lock_wait_ms, got: {alerts}"
        
        # Verify critical alert for conflict_rate (>40 threshold)
        critical_conflict_alert = next(
            (alert for alert in alerts 
             if alert.get("metric") == "conflict_rate" and alert.get("severity") == "critical"),
            None
        )
        assert critical_conflict_alert is not None, f"Expected critical alert for conflict_rate, got: {alerts}"

    def test_simulate_warning_level_alerts(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 150,  # > 120 warning
                "max_lock_wait_ms": 300,  # > 250 warning
                "publish_duration_ms_p95": 1200,  # > 1000 warning
                "conflict_rate": 30,  # > 25 warning
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        
        alerts = response.json().get("alerts") or []
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        assert len(warning_alerts) >= 3, f"Expected at least 3 warning alerts, got: {alerts}"


class TestPublishAuditsEndpoint:
    """GET /api/admin/ui/configs/{config_type}/publish-audits - KPI + telemetry + windows + trends"""

    def test_publish_audits_returns_telemetry_and_kpi(self, admin_token: str):
        # First create and publish a draft to generate audit data
        scope_id = f"p67-audit-{uuid.uuid4().hex[:8]}"
        draft = _create_dashboard_draft(admin_token, scope_id, title="Audit test")
        
        # Publish to generate audit entry
        requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": draft.get("id"),
                "config_version": draft.get("version"),
                "resolved_config_hash": draft.get("resolved_config_hash"),
                "owner_type": "dealer",
                "owner_id": scope_id,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        
        # Now fetch audits
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish-audits?segment=corporate&scope=tenant&scope_id={scope_id}&limit=50",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Publish audits failed: {response.text[:300]}"
        
        payload = response.json()
        
        # Verify items structure
        assert isinstance(payload.get("items"), list)
        
        # Verify telemetry structure
        telemetry = payload.get("telemetry") or {}
        assert "avg_lock_wait_ms" in telemetry
        assert "max_lock_wait_ms" in telemetry
        assert "publish_duration_ms_p95" in telemetry
        assert "conflict_rate" in telemetry
        assert "publish_success_rate" in telemetry
        
        # Verify KPI structure
        kpi = payload.get("kpi") or {}
        assert "median_retry_count" in kpi
        assert "time_to_publish_ms" in kpi
        assert "conflict_resolution_time_ms" in kpi
        assert "publish_success_rate" in kpi
        
        # Verify windows (1h/24h/7d) structure
        windows = payload.get("windows") or {}
        assert "1h" in windows
        assert "24h" in windows
        assert "7d" in windows
        
        # Verify trends structure (24h sparkline)
        trends = payload.get("trends") or {}
        assert trends.get("window") == "24h"
        assert isinstance(trends.get("points"), list)
        
        # Verify thresholds are included
        assert "thresholds" in payload


class TestConflictSyncEndpoint:
    """POST /api/admin/ui/configs/{config_type}/conflict-sync - latest draft + diff"""

    def test_conflict_sync_returns_latest_draft_and_diff(self, admin_token: str):
        scope_id = f"p67-sync-{uuid.uuid4().hex[:8]}"
        
        # Create first draft
        first = _create_dashboard_draft(admin_token, scope_id, title="Draft v1")
        
        # Create second draft (simulating conflict scenario)
        second = _create_dashboard_draft(admin_token, scope_id, title="Draft v2")
        
        # Call conflict-sync with first version
        response = requests.post(
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
        assert response.status_code == 200, f"Conflict sync failed: {response.text[:300]}"
        
        payload = response.json()
        
        # Verify returns latest draft
        assert payload.get("item", {}).get("version") == second.get("version")
        
        # Verify items list
        assert isinstance(payload.get("items"), list)
        
        # Verify diff is returned
        diff = payload.get("diff") or {}
        assert diff.get("config_type") == "dashboard"
        
        # Verify from_item and to_item for visual diff
        assert "from_item" in payload
        assert "to_item" in payload


class TestIntegrationScenario:
    """End-to-end test: create draft -> publish -> check audits -> rollback"""

    def test_full_publish_workflow_with_telemetry_tracking(self, admin_token: str):
        scope_id = f"p67-e2e-{uuid.uuid4().hex[:8]}"
        
        # Step 1: Create draft
        draft = _create_dashboard_draft(admin_token, scope_id, title="E2E Test")
        assert draft.get("id") is not None
        
        # Step 2: Publish
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": draft.get("id"),
                "config_version": draft.get("version"),
                "resolved_config_hash": draft.get("resolved_config_hash"),
                "owner_type": "dealer",
                "owner_id": scope_id,
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert publish_response.status_code == 200
        
        # Step 3: Check publish audits
        audits_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish-audits?segment=corporate&scope=tenant&scope_id={scope_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert audits_response.status_code == 200
        audits = audits_response.json()
        assert audits.get("telemetry") is not None
        assert audits.get("kpi") is not None
        assert audits.get("windows") is not None
        
        # Step 4: Verify legacy endpoint still returns 410
        legacy_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/{draft.get('id')}",
            json={"config_version": draft.get("version")},
            headers=_headers(admin_token),
        )
        assert legacy_response.status_code == 410
