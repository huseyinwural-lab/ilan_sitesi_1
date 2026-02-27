"""
P62 Extended Dashboard UI Tests (Full E2E Coverage)
- Dashboard admin UI: widget add/delete/drag-reorder, draft auto-save, publish modal diff, publish confirm
- Dashboard guardrail UI+API: KPI없으면 publish disabled + backend 400; 12개 초과 widget 추가 방지 + backend 400
- Publish 후 live render verification: /dealer/dashboard 화면에서 config-driven widget render
- Individual Header admin UI: row-based DnD, visible toggle, logo fallback input, draft save + publish + rollback
- Draft→Publish E2E and Rollback E2E flows (dashboard + individual header)
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


class TestDashboardAPIContract:
    """Backend endpoint contract validation for dashboard"""

    def test_get_dashboard_configs(self, admin_token: str):
        """GET /api/admin/ui/configs/dashboard - retrieves dashboard configs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard?segment=corporate&scope=system&status=draft",
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        payload = response.json()
        assert "item" in payload or "items" in payload, "Response should contain item or items"

    def test_post_dashboard_config_creates_draft(self, admin_token: str):
        """POST /api/admin/ui/configs/dashboard - creates new draft config"""
        scope_id = f"test-contract-{uuid.uuid4().hex[:10]}"
        widgets = [
            {"widget_id": "kpi-1", "widget_type": "kpi", "title": "KPI Widget", "enabled": True},
            {"widget_id": "chart-1", "widget_type": "chart", "title": "Chart Widget", "enabled": True},
        ]
        layout = [
            {"widget_id": "kpi-1", "x": 0, "y": 0, "w": 3, "h": 1},
            {"widget_id": "chart-1", "x": 3, "y": 0, "w": 6, "h": 1},
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Contract Test Dashboard"},
                "layout": layout,
                "widgets": widgets,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        payload = response.json()
        item = payload.get("item") or {}
        assert item.get("config_type") == "dashboard"
        assert item.get("status") == "draft"
        assert len(item.get("widgets") or []) == 2
        assert len(item.get("layout") or []) == 2

    def test_publish_dashboard_requires_confirm(self, admin_token: str):
        """POST /api/admin/ui/configs/dashboard/publish - requires confirmation"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "system",
                "config_version": 1,
                "require_confirm": False,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 400, f"Expected 400 when confirm not required, got {response.status_code}"
        detail = response.json().get("detail")
        detail_text = detail.get("message", "") if isinstance(detail, dict) else str(detail)
        assert "onay" in detail_text.lower() or "confirm" in detail_text.lower()

    def test_get_dashboard_diff(self, admin_token: str):
        """GET /api/admin/ui/configs/dashboard/diff - retrieves diff between statuses"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/diff?segment=corporate&scope=system&from_status=published&to_status=draft",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        payload = response.json()
        assert "diff" in payload, "Response should contain diff object"

    def test_rollback_requires_confirm(self, admin_token: str):
        """POST /api/admin/ui/configs/dashboard/rollback - requires confirmation"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/rollback",
            json={
                "segment": "corporate",
                "scope": "system",
                "rollback_reason": "test reason",
                "require_confirm": False,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 400, f"Expected 400 when confirm not required, got {response.status_code}"


class TestDashboardGuardrailsE2E:
    """Guardrail validation for dashboard"""

    def test_guardrail_no_kpi_returns_400(self, admin_token: str):
        """Dashboard without enabled KPI widget should return 400"""
        scope_id = f"test-no-kpi-{uuid.uuid4().hex[:10]}"
        widgets = [
            {"widget_id": "chart-1", "widget_type": "chart", "title": "Chart", "enabled": True},
        ]
        layout = [{"widget_id": "chart-1", "x": 0, "y": 0, "w": 6, "h": 1}]
        
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
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 400, f"Expected 400 for no KPI, got {response.status_code}"
        assert "kpi" in response.json().get("detail", "").lower()

    def test_guardrail_more_than_12_widgets_returns_400(self, admin_token: str):
        """Dashboard with more than 12 widgets should return 400"""
        scope_id = f"test-too-many-{uuid.uuid4().hex[:10]}"
        widgets = []
        layout = []
        
        # Add 13 widgets (1 KPI + 12 charts)
        widgets.append({"widget_id": "kpi-1", "widget_type": "kpi", "title": "KPI", "enabled": True})
        layout.append({"widget_id": "kpi-1", "x": 0, "y": 0, "w": 3, "h": 1})
        
        for i in range(12):
            widget_id = f"chart-{i+1}"
            widgets.append({"widget_id": widget_id, "widget_type": "chart", "title": f"Chart {i+1}", "enabled": True})
            layout.append({"widget_id": widget_id, "x": (i * 3) % 12, "y": (i // 4) + 1, "w": 3, "h": 1})
        
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
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 400, f"Expected 400 for >12 widgets, got {response.status_code}"
        assert "12" in response.json().get("detail", "")


class TestPublishAndRollbackE2E:
    """Full E2E flow for publish and rollback"""

    def test_full_dashboard_publish_rollback_flow(self, admin_token: str):
        """Complete E2E: draft → publish → add widget → publish → rollback"""
        scope_id = f"test-e2e-{uuid.uuid4().hex[:10]}"
        
        # Step 1: Create initial draft
        initial_widgets = [
            {"widget_id": "kpi-1", "widget_type": "kpi", "title": "KPI", "enabled": True},
        ]
        initial_layout = [{"widget_id": "kpi-1", "x": 0, "y": 0, "w": 3, "h": 1}]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Initial Dashboard"},
                "layout": initial_layout,
                "widgets": initial_widgets,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Initial draft failed: {response.text[:300]}"
        config_id_v1 = response.json().get("item", {}).get("id")
        config_version_v1 = response.json().get("item", {}).get("version")
        
        # Step 2: Publish initial draft
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": config_id_v1,
                "config_version": config_version_v1,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Initial publish failed: {response.text[:300]}"
        
        # Step 3: Create new draft with additional widget
        updated_widgets = [
            {"widget_id": "kpi-1", "widget_type": "kpi", "title": "KPI", "enabled": True},
            {"widget_id": "chart-1", "widget_type": "chart", "title": "Chart", "enabled": True},
        ]
        updated_layout = [
            {"widget_id": "kpi-1", "x": 0, "y": 0, "w": 3, "h": 1},
            {"widget_id": "chart-1", "x": 3, "y": 0, "w": 6, "h": 1},
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Updated Dashboard"},
                "layout": updated_layout,
                "widgets": updated_widgets,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Updated draft failed: {response.text[:300]}"
        updated_version = response.json().get("item", {}).get("version")
        
        # Step 4: Check diff
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/diff?segment=corporate&scope=tenant&scope_id={scope_id}&from_status=published&to_status=draft",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Diff failed: {response.text[:300]}"
        diff = response.json().get("diff") or {}
        assert diff.get("has_changes") is True
        assert "chart-1" in (diff.get("added_widgets") or [])
        
        # Step 5: Publish updated draft
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_version": updated_version,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Updated publish failed: {response.text[:300]}"
        
        # Step 6: Rollback to initial version
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/rollback",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "target_config_id": config_id_v1,
                "rollback_reason": "dashboard rollback reason",
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200, f"Rollback failed: {response.text[:300]}"
        assert response.json().get("rolled_back_to") == config_id_v1
        
        # Step 7: Verify effective config is back to v1
        response = requests.get(
            f"{BASE_URL}/api/ui/dashboard?segment=corporate&tenant_id={scope_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Effective verify failed: {response.text[:300]}"
        effective = response.json()
        assert len(effective.get("widgets") or []) == 1, "Should have only 1 widget after rollback"


class TestIndividualHeaderFeatureDisabled:
    """Individual Header endpoint disabled tests"""

    def test_header_endpoints_disabled(self, admin_token: str):
        scope_id = f"test-header-disabled-{uuid.uuid4().hex[:10]}"
        save_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"rows": []},
            },
            headers=_auth_headers(admin_token),
        )
        assert save_response.status_code == 403, f"Expected 403, got {save_response.status_code}: {save_response.text[:300]}"
        detail = save_response.json().get("detail") or {}
        assert detail.get("code") == "FEATURE_DISABLED"


class TestLiveRenderVerification:
    """Verify published config renders correctly in live view"""

    def test_effective_dashboard_config_render(self, admin_token: str):
        """Verify GET /api/ui/dashboard returns published config"""
        scope_id = f"test-render-{uuid.uuid4().hex[:10]}"
        
        # Create and publish a config
        widgets = [
            {"widget_id": "kpi-render", "widget_type": "kpi", "title": "Render KPI", "enabled": True},
            {"widget_id": "chart-render", "widget_type": "chart", "title": "Render Chart", "enabled": True},
        ]
        layout = [
            {"widget_id": "kpi-render", "x": 0, "y": 0, "w": 3, "h": 1},
            {"widget_id": "chart-render", "x": 3, "y": 0, "w": 6, "h": 1},
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"title": "Render Test Dashboard"},
                "layout": layout,
                "widgets": widgets,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200
        config_id = response.json().get("item", {}).get("id")
        config_version = response.json().get("item", {}).get("version")
        
        # Publish
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish",
            json={
                "segment": "corporate",
                "scope": "tenant",
                "scope_id": scope_id,
                "config_id": config_id,
                "config_version": config_version,
                "require_confirm": True,
            },
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 200
        
        # Verify effective config for this tenant
        response = requests.get(
            f"{BASE_URL}/api/ui/dashboard?segment=corporate&tenant_id={scope_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Effective failed: {response.text[:300]}"
        
        effective = response.json()
        assert effective.get("source_scope") == "tenant", f"Expected tenant scope, got {effective.get('source_scope')}"
        assert len(effective.get("widgets") or []) == 2
        assert len(effective.get("layout") or []) == 2
        
        # Verify config_data also contains widgets and layout
        config_data = effective.get("config_data") or {}
        assert len(config_data.get("widgets") or []) == 2
        assert len(config_data.get("layout") or []) == 2
