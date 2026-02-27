"""
P1 Ops Publish Health + Alert Reliability tests
- GET /api/admin/ops/alert-delivery-metrics?window=24h
- POST /api/admin/ops/alert-delivery/rerun-simulation
"""
import os
import time

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


def _login(email: str, password: str, portal: str):
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"X-Portal-Scope": portal},
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed for {email}: {response.status_code} - {response.text[:200]}")
    payload = response.json()
    return payload.get("access_token") or payload.get("token")


def _headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")


@pytest.fixture(scope="module")
def dealer_token():
    return _login(DEALER_EMAIL, DEALER_PASSWORD, "dealer")


class TestAlertDeliveryMetricsEndpoint:
    def test_alert_delivery_metrics_returns_server_side_kpi(self, admin_token: str):
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"

        payload = response.json()
        assert payload.get("window") == "24h"
        assert "total_attempts" in payload
        assert "successful_deliveries" in payload
        assert "failed_deliveries" in payload
        assert "success_rate" in payload

        breakdown = payload.get("channel_breakdown") or {}
        assert "slack" in breakdown
        assert "smtp" in breakdown
        assert "pd" in breakdown

    def test_alert_delivery_metrics_rejects_window_gt_24h(self, admin_token: str):
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=48h",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"
        detail = response.json().get("detail") or {}
        assert detail.get("code") == "INVALID_WINDOW"


class TestRerunSimulationSecurityAndRateLimit:
    def test_rerun_requires_admin_or_ops_role(self, dealer_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            json={"config_type": "dashboard"},
            headers=_headers(dealer_token),
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text[:300]}"

    def test_rerun_creates_trigger_audit_fields(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            json={"config_type": "dashboard"},
            headers=_headers(admin_token),
        )

        if response.status_code == 429:
            retry_after = int((response.json().get("detail") or {}).get("retry_after_seconds") or 1)
            pytest.skip(f"Rate limiter active from prior calls. retry_after={retry_after}s")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        payload = response.json()
        assert payload.get("correlation_id")
        assert payload.get("delivery_status") in {"ok", "partial_fail", "blocked_missing_secrets"}

    def test_rerun_rate_limit_enforced_max_3_per_minute(self, admin_token: str):
        statuses = []
        for _ in range(4):
            response = requests.post(
                f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
                json={"config_type": "dashboard"},
                headers=_headers(admin_token),
            )
            statuses.append(response.status_code)
            if response.status_code == 429:
                detail = response.json().get("detail") or {}
                assert detail.get("code") == "RATE_LIMITED"
                assert int(detail.get("limit_per_minute") or 0) == 3
                break
            time.sleep(0.2)

        assert 429 in statuses, f"Expected 429 in statuses, got: {statuses}"