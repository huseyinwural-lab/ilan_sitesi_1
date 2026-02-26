"""
P61 Dashboard backend tests
- ui_configs.layout/widgets persistence
- Dashboard guardrails: min 1 KPI, max 12 widget
- Draft -> publish -> effective resolve
"""
import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


def _get_admin_token() -> str:
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"X-Portal-Scope": "admin"},
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text[:200]}")
    payload = response.json()
    return payload.get("access_token") or payload.get("token")


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _get_admin_token()


def _build_widgets(count: int, include_kpi: bool) -> list[dict]:
    widgets = []
    for idx in range(count):
        widget_id = f"w-{idx + 1}"
        widget_type = "kpi" if include_kpi and idx == 0 else "chart"
        widgets.append(
            {
                "widget_id": widget_id,
                "widget_type": widget_type,
                "title": f"Widget {idx + 1}",
                "enabled": True,
            }
        )
    return widgets


def _build_layout(widget_ids: list[str]) -> list[dict]:
    layout = []
    for idx, widget_id in enumerate(widget_ids):
        layout.append(
            {
                "widget_id": widget_id,
                "x": (idx * 3) % 12,
                "y": idx // 4,
                "w": 3,
                "h": 1,
            }
        )
    return layout


class TestDashboardGuardrailsAndPersistence:
    def test_dashboard_save_draft_valid(self, admin_token: str):
        scope_id = f"tenant-p61-{uuid.uuid4().hex[:10]}"
        widgets = _build_widgets(3, include_kpi=True)
        layout = _build_layout([w["widget_id"] for w in widgets])

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Dealer Dashboard"},
                "layout": layout,
                "widgets": widgets,
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        payload = response.json()
        item = payload.get("item") or {}
        assert item.get("config_type") == "dashboard"
        assert item.get("status") == "draft"
        assert len(item.get("layout") or []) == 3
        assert len(item.get("widgets") or []) == 3

    def test_dashboard_save_rejects_without_kpi(self, admin_token: str):
        scope_id = f"tenant-p61-{uuid.uuid4().hex[:10]}"
        widgets = _build_widgets(2, include_kpi=False)
        layout = _build_layout([w["widget_id"] for w in widgets])

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {},
                "layout": layout,
                "widgets": widgets,
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"
        assert "kpi" in (response.json().get("detail") or "").lower()

    def test_dashboard_save_rejects_more_than_12_widgets(self, admin_token: str):
        scope_id = f"tenant-p61-{uuid.uuid4().hex[:10]}"
        widgets = _build_widgets(13, include_kpi=True)
        layout = _build_layout([w["widget_id"] for w in widgets])

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {},
                "layout": layout,
                "widgets": widgets,
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"
        assert "12" in (response.json().get("detail") or "")

    def test_dashboard_publish_and_effective(self, admin_token: str):
        scope_id = f"tenant-p61-{uuid.uuid4().hex[:10]}"
        widgets = _build_widgets(4, include_kpi=True)
        layout = _build_layout([w["widget_id"] for w in widgets])

        save_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Draft Dashboard"},
                "layout": layout,
                "widgets": widgets,
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        )
        assert save_response.status_code == 200, f"Draft save failed: {save_response.text[:300]}"
        config_id = save_response.json().get("item", {}).get("id")
        assert config_id, "Draft config_id missing"

        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/{config_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert publish_response.status_code == 200, f"Publish failed: {publish_response.text[:300]}"
        published_item = publish_response.json().get("item") or {}
        assert published_item.get("status") == "published"
        assert len(published_item.get("widgets") or []) == 4

        effective_response = requests.get(
            f"{BASE_URL}/api/ui/dashboard?segment=corporate&tenant_id={scope_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert effective_response.status_code == 200, f"Effective resolve failed: {effective_response.text[:300]}"
        effective_payload = effective_response.json()
        assert effective_payload.get("source_scope") == "tenant"
        assert len(effective_payload.get("widgets") or []) == 4
        assert len((effective_payload.get("config_data") or {}).get("widgets") or []) == 4
