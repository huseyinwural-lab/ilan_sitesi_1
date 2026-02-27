"""
P62 UI publish workflow tests
- publish confirmation endpoint
- draft->diff->publish->rollback flow (dashboard)
- diff/publish/rollback flow (individual header)
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


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _build_dashboard_widgets(count: int) -> list[dict]:
    rows = []
    for index in range(count):
        widget_type = "kpi" if index == 0 else "chart"
        rows.append(
            {
                "widget_id": f"widget-{index + 1}",
                "widget_type": widget_type,
                "title": f"Widget {index + 1}",
                "enabled": True,
            }
        )
    return rows


def _build_dashboard_layout(widget_ids: list[str]) -> list[dict]:
    layout = []
    for index, widget_id in enumerate(widget_ids):
        layout.append(
            {
                "widget_id": widget_id,
                "x": (index * 3) % 12,
                "y": index // 4,
                "w": 3,
                "h": 1,
            }
        )
    return layout


class TestUIPublishWorkflow:
    def test_publish_latest_requires_confirm(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "system",
                "require_confirm": False,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:300]}"

    def test_dashboard_diff_publish_rollback_flow(self, admin_token: str):
        scope_id = f"tenant-p62-{uuid.uuid4().hex[:10]}"

        baseline_widgets = _build_dashboard_widgets(2)
        baseline_layout = _build_dashboard_layout([item["widget_id"] for item in baseline_widgets])

        save_baseline = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Baseline"},
                "layout": baseline_layout,
                "widgets": baseline_widgets,
            },
            headers=_auth_headers(admin_token),
        )
        assert save_baseline.status_code == 200, f"Baseline draft save failed: {save_baseline.text[:300]}"
        baseline_id = save_baseline.json().get("item", {}).get("id")
        baseline_version = save_baseline.json().get("item", {}).get("version")
        assert baseline_id

        publish_baseline = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": baseline_id,
                "config_version": baseline_version,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert publish_baseline.status_code == 200, f"Baseline publish failed: {publish_baseline.text[:300]}"

        next_widgets = baseline_widgets + [
            {
                "widget_id": "widget-3",
                "widget_type": "list",
                "title": "Yeni Liste",
                "enabled": True,
            }
        ]
        next_layout = _build_dashboard_layout([item["widget_id"] for item in next_widgets])
        next_layout[0]["x"] = 6

        save_next = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Draft Next"},
                "layout": next_layout,
                "widgets": next_widgets,
            },
            headers=_auth_headers(admin_token),
        )
        assert save_next.status_code == 200, f"Next draft save failed: {save_next.text[:300]}"
        next_version = save_next.json().get("item", {}).get("version")

        diff_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/diff?segment=corporate&scope=tenant&scope_id={scope_id}&from_status=published&to_status=draft",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert diff_response.status_code == 200, f"Diff failed: {diff_response.text[:300]}"
        diff_payload = diff_response.json().get("diff") or {}
        assert diff_payload.get("has_changes") is True
        assert "widget-3" in (diff_payload.get("added_widgets") or [])

        publish_next = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_version": next_version,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert publish_next.status_code == 200, f"Next publish failed: {publish_next.text[:300]}"

        rollback_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/rollback",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "target_config_id": baseline_id,
                "rollback_reason": "publish regression rollback",
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert rollback_response.status_code == 200, f"Rollback failed: {rollback_response.text[:300]}"
        rolled = rollback_response.json()
        assert rolled.get("rolled_back_to") == baseline_id

    def test_individual_header_diff_publish_rollback(self, admin_token: str):
        scope_id = f"tenant-p62-header-{uuid.uuid4().hex[:10]}"

        baseline_header = {
            "rows": [
                {
                    "id": "row1",
                    "title": "Row 1",
                    "visible": True,
                    "blocks": [
                        {"id": "logo", "type": "logo", "label": "Logo", "visible": True},
                        {"id": "search", "type": "search", "label": "Arama", "visible": True},
                    ],
                },
                {
                    "id": "row2",
                    "title": "Row 2",
                    "visible": True,
                    "blocks": [
                        {"id": "quick-links", "type": "quick_links", "label": "Hızlı Link", "visible": True},
                    ],
                },
            ],
            "logo": {"fallback_text": "ANNONCIA"},
        }

        save_baseline = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": baseline_header,
            },
            headers=_auth_headers(admin_token),
        )
        assert save_baseline.status_code == 200, f"Baseline header save failed: {save_baseline.text[:300]}"
        baseline_id = save_baseline.json().get("item", {}).get("id")
        baseline_version = save_baseline.json().get("item", {}).get("version")
        assert baseline_id

        publish_baseline = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/publish",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": baseline_id,
                "config_version": baseline_version,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert publish_baseline.status_code == 200, f"Baseline header publish failed: {publish_baseline.text[:300]}"

        next_header = {
            "rows": [
                {
                    "id": "row1",
                    "title": "Row 1",
                    "visible": True,
                    "blocks": [
                        {"id": "logo", "type": "logo", "label": "Logo", "visible": True},
                    ],
                },
                {
                    "id": "row2",
                    "title": "Row 2",
                    "visible": True,
                    "blocks": [
                        {"id": "quick-links", "type": "quick_links", "label": "Hızlı Link", "visible": False},
                        {"id": "search", "type": "search", "label": "Arama", "visible": True},
                    ],
                },
            ],
            "logo": {"fallback_text": "ANNONCIA"},
        }

        save_next = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": next_header,
            },
            headers=_auth_headers(admin_token),
        )
        assert save_next.status_code == 200, f"Next header save failed: {save_next.text[:300]}"
        next_version = save_next.json().get("item", {}).get("version")

        diff_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header/diff?segment=individual&scope=tenant&scope_id={scope_id}&from_status=published&to_status=draft",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert diff_response.status_code == 200, f"Header diff failed: {diff_response.text[:300]}"
        diff_payload = diff_response.json().get("diff") or {}
        assert diff_payload.get("has_changes") is True

        publish_next = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/publish",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_version": next_version,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert publish_next.status_code == 200, f"Header publish failed: {publish_next.text[:300]}"

        rollback_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/rollback",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "target_config_id": baseline_id,
                "rollback_reason": "header rollback reason",
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert rollback_response.status_code == 200, f"Header rollback failed: {rollback_response.text[:300]}"
        assert rollback_response.json().get("rolled_back_to") == baseline_id
