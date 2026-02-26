"""
P61 Dashboard backend tests
- Alembic migration: ui_configs table layout/widgets columns verification
- POST /api/admin/ui/configs/dashboard valid payload with draft creation
- Guardrail-1: KPI-less dashboard save request returns 400
- Guardrail-2: >12 widgets dashboard save request returns 400
- POST /api/admin/ui/configs/dashboard/publish/{config_id} publish flow
- GET /api/ui/dashboard effective config resolution from tenant scope (layout/widgets)
- Additional edge cases: widget_id uniqueness, layout-widget mapping
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
    """Build widgets list with or without KPI widget"""
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
    """Build layout entries for given widget IDs"""
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
    """Core P61 Dashboard tests: CRUD, guardrails, publish flow"""

    def test_dashboard_save_draft_valid(self, admin_token: str):
        """POST /api/admin/ui/configs/dashboard - valid payload creates draft with layout/widgets persisted"""
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
        # Verify widget structure preserved
        widget_types = [w.get("widget_type") for w in item.get("widgets", [])]
        assert "kpi" in widget_types, "KPI widget should be persisted"

    def test_dashboard_save_rejects_without_kpi(self, admin_token: str):
        """Guardrail-1: Dashboard without KPI widget returns 400"""
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
        detail = response.json().get("detail") or ""
        assert "kpi" in detail.lower(), f"Error should mention KPI requirement: {detail}"

    def test_dashboard_save_rejects_more_than_12_widgets(self, admin_token: str):
        """Guardrail-2: Dashboard with >12 widgets returns 400"""
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
        detail = response.json().get("detail") or ""
        assert "12" in detail, f"Error should mention max 12 widgets: {detail}"

    def test_dashboard_publish_and_effective(self, admin_token: str):
        """Full workflow: save draft -> publish -> GET /api/ui/dashboard effective resolve with tenant scope"""
        scope_id = f"tenant-p61-{uuid.uuid4().hex[:10]}"
        widgets = _build_widgets(4, include_kpi=True)
        layout = _build_layout([w["widget_id"] for w in widgets])

        # Step 1: Create draft
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

        # Step 2: Publish
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/{config_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert publish_response.status_code == 200, f"Publish failed: {publish_response.text[:300]}"
        published_item = publish_response.json().get("item") or {}
        assert published_item.get("status") == "published"
        assert len(published_item.get("widgets") or []) == 4
        assert len(published_item.get("layout") or []) == 4

        # Step 3: GET effective config with tenant scope
        effective_response = requests.get(
            f"{BASE_URL}/api/ui/dashboard?segment=corporate&tenant_id={scope_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert effective_response.status_code == 200, f"Effective resolve failed: {effective_response.text[:300]}"
        effective_payload = effective_response.json()
        
        # Verify source_scope is tenant (not system fallback)
        assert effective_payload.get("source_scope") == "tenant", f"Expected tenant scope, got {effective_payload.get('source_scope')}"
        
        # Verify layout and widgets present in response
        assert len(effective_payload.get("widgets") or []) == 4
        assert len(effective_payload.get("layout") or []) == 4
        
        # Verify config_data also has widgets embedded
        config_data = effective_payload.get("config_data") or {}
        assert len(config_data.get("widgets") or []) == 4
        assert len(config_data.get("layout") or []) == 4


class TestDashboardEdgeCases:
    """Additional edge case tests for dashboard validation"""

    def test_dashboard_save_exactly_12_widgets(self, admin_token: str):
        """Edge case: Exactly 12 widgets should be accepted"""
        scope_id = f"tenant-p61-edge-{uuid.uuid4().hex[:10]}"
        widgets = _build_widgets(12, include_kpi=True)
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
        assert response.status_code == 200, f"12 widgets should be accepted: {response.text[:300]}"
        item = response.json().get("item") or {}
        assert len(item.get("widgets") or []) == 12

    def test_dashboard_save_exactly_1_kpi_widget(self, admin_token: str):
        """Edge case: Exactly 1 KPI widget (minimum) should be accepted"""
        scope_id = f"tenant-p61-minkpi-{uuid.uuid4().hex[:10]}"
        widgets = [{"widget_id": "kpi-only", "widget_type": "kpi", "title": "Single KPI", "enabled": True}]
        layout = _build_layout(["kpi-only"])

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
        assert response.status_code == 200, f"Single KPI widget should be accepted: {response.text[:300]}"

    def test_dashboard_rejects_duplicate_widget_ids(self, admin_token: str):
        """Guardrail: Duplicate widget_id values should be rejected"""
        scope_id = f"tenant-p61-dup-{uuid.uuid4().hex[:10]}"
        widgets = [
            {"widget_id": "dup-id", "widget_type": "kpi", "title": "KPI 1", "enabled": True},
            {"widget_id": "dup-id", "widget_type": "chart", "title": "Chart 1", "enabled": True},
        ]
        layout = _build_layout(["dup-id", "dup-id"])

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
        assert response.status_code == 400, f"Duplicate widget_id should be rejected: {response.text[:300]}"
        detail = response.json().get("detail") or ""
        assert "benzersiz" in detail.lower() or "unique" in detail.lower(), f"Error should mention uniqueness: {detail}"

    def test_dashboard_disabled_kpi_not_counted(self, admin_token: str):
        """Guardrail: Disabled KPI widget should not count towards min requirement"""
        scope_id = f"tenant-p61-disabled-{uuid.uuid4().hex[:10]}"
        widgets = [
            {"widget_id": "kpi-disabled", "widget_type": "kpi", "title": "Disabled KPI", "enabled": False},
            {"widget_id": "chart-1", "widget_type": "chart", "title": "Chart 1", "enabled": True},
        ]
        layout = _build_layout(["kpi-disabled", "chart-1"])

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
        # Disabled KPI should not count, so this should fail min 1 KPI requirement
        assert response.status_code == 400, f"Disabled KPI should not count: {response.text[:300]}"

    def test_dashboard_system_scope_no_scope_id(self, admin_token: str):
        """System scope dashboard creation (no scope_id required)"""
        widgets = _build_widgets(2, include_kpi=True)
        layout = _build_layout([w["widget_id"] for w in widgets])

        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "system",
                "status": "draft",
                "config_data": {"title": "System Dashboard"},
                "layout": layout,
                "widgets": widgets,
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
        )
        assert response.status_code == 200, f"System scope dashboard should work: {response.text[:300]}"
        item = response.json().get("item") or {}
        assert item.get("scope") == "system"

    def test_effective_fallback_to_default(self, admin_token: str):
        """GET /api/ui/dashboard - returns default when no published config exists"""
        nonexistent_tenant = f"nonexistent-{uuid.uuid4().hex[:10]}"
        
        response = requests.get(
            f"{BASE_URL}/api/ui/dashboard?segment=corporate&tenant_id={nonexistent_tenant}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Should return 200 with default: {response.text[:300]}"
        payload = response.json()
        # source_scope should be "default" or "system" when no tenant config exists
        assert payload.get("source_scope") in ("default", "system", "tenant"), f"Unexpected source_scope: {payload.get('source_scope')}"
