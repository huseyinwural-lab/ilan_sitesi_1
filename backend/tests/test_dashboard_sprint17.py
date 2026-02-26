"""
Backend tests for Iteration 17:
- Dashboard summary endpoint (kpis, trends, risk_panel)
- KPI links validation
- Menu Management API disabled (403 + feature_disabled)
- Category import/export CSV-only (XLSX returns 403)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Login as admin and get token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


# ==== Dashboard Summary Tests ====

class TestDashboardSummary:
    """Tests for /api/admin/dashboard/summary endpoint"""

    def test_dashboard_summary_returns_200(self, auth_headers):
        """GET /api/admin/dashboard/summary should return 200"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard summary failed: {response.status_code} - {response.text}"

    def test_dashboard_summary_has_kpis(self, auth_headers):
        """Dashboard summary should have kpis object with today and last_7_days"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "kpis" in data, "kpis missing from response"
        kpis = data["kpis"]
        
        assert "today" in kpis, "kpis.today missing"
        assert "last_7_days" in kpis, "kpis.last_7_days missing"
        
        # Verify today structure
        today = kpis["today"]
        assert "new_listings" in today, "kpis.today.new_listings missing"
        assert "new_users" in today, "kpis.today.new_users missing"
        assert "revenue_total" in today, "kpis.today.revenue_total missing"
        
        # Verify last_7_days structure  
        week = kpis["last_7_days"]
        assert "new_listings" in week, "kpis.last_7_days.new_listings missing"
        assert "new_users" in week, "kpis.last_7_days.new_users missing"
        assert "revenue_total" in week, "kpis.last_7_days.revenue_total missing"

    def test_dashboard_summary_has_trends(self, auth_headers):
        """Dashboard summary should have trends object with listings array"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "trends" in data, "trends missing from response"
        trends = data["trends"]
        
        assert "window_days" in trends, "trends.window_days missing"
        assert "listings" in trends, "trends.listings missing"
        assert isinstance(trends["listings"], list), "trends.listings should be a list"

    def test_dashboard_summary_has_risk_panel(self, auth_headers):
        """Dashboard summary should have risk_panel object"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "risk_panel" in data, "risk_panel missing from response"
        risk = data["risk_panel"]
        
        assert "suspicious_logins" in risk, "risk_panel.suspicious_logins missing"
        assert "sla_breaches" in risk, "risk_panel.sla_breaches missing"
        assert "pending_payments" in risk, "risk_panel.pending_payments missing"
        
        # Verify structure
        assert "count" in risk["suspicious_logins"], "suspicious_logins.count missing"
        assert "count" in risk["sla_breaches"], "sla_breaches.count missing"
        assert "count" in risk["pending_payments"], "pending_payments.count missing"

    def test_dashboard_summary_has_kpi_links(self, auth_headers):
        """Dashboard summary should have kpi_links with today and last_7_days URLs"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "kpi_links" in data, "kpi_links missing from response"
        kpi_links = data["kpi_links"]
        
        assert "today" in kpi_links, "kpi_links.today missing"
        assert "last_7_days" in kpi_links, "kpi_links.last_7_days missing"
        
        # Verify correct URLs
        assert kpi_links["today"] == "/admin/listings?period=today", \
            f"Expected '/admin/listings?period=today', got '{kpi_links['today']}'"
        assert kpi_links["last_7_days"] == "/admin/listings?period=last_7_days", \
            f"Expected '/admin/listings?period=last_7_days', got '{kpi_links['last_7_days']}'"


# ==== Menu Management Disabled Tests ====

class TestMenuManagementDisabled:
    """Menu Management API endpoints should return 403 + feature_disabled"""

    def test_get_menu_items_returns_403(self, auth_headers):
        """GET /api/admin/menu-items should return 403 with feature_disabled"""
        response = requests.get(f"{BASE_URL}/api/admin/menu-items", headers=auth_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected 'feature_disabled', got {data}"

    def test_post_menu_items_returns_403(self, auth_headers):
        """POST /api/admin/menu-items should return 403 with feature_disabled"""
        payload = {"label": "Test", "slug": "test", "url": "/test"}
        response = requests.post(f"{BASE_URL}/api/admin/menu-items", headers=auth_headers, json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected 'feature_disabled', got {data}"

    def test_patch_menu_items_returns_403(self, auth_headers):
        """PATCH /api/admin/menu-items/{id} should return 403 with feature_disabled"""
        fake_id = "00000000-0000-0000-0000-000000000001"
        payload = {"label": "Updated"}
        response = requests.patch(f"{BASE_URL}/api/admin/menu-items/{fake_id}", headers=auth_headers, json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected 'feature_disabled', got {data}"

    def test_delete_menu_items_returns_403(self, auth_headers):
        """DELETE /api/admin/menu-items/{id} should return 403 with feature_disabled"""
        fake_id = "00000000-0000-0000-0000-000000000001"
        response = requests.delete(f"{BASE_URL}/api/admin/menu-items/{fake_id}", headers=auth_headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected 'feature_disabled', got {data}"


# ==== Category Import/Export CSV-Only Tests ====

class TestCategoryImportExportCsvOnly:
    """Category import/export should only allow CSV (XLSX returns 403)"""

    def test_csv_export_returns_200(self, auth_headers):
        """GET /api/admin/categories/import-export/export/csv should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/export/csv",
            headers=auth_headers,
            params={"module": "vehicle", "country": "DE"}
        )
        assert response.status_code == 200, f"CSV export failed: {response.status_code} - {response.text}"
        assert "text/csv" in response.headers.get("content-type", ""), \
            f"Expected CSV content-type, got {response.headers.get('content-type')}"

    def test_csv_sample_returns_200(self, auth_headers):
        """GET /api/admin/categories/import-export/sample/csv should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/sample/csv",
            headers=auth_headers,
            params={"module": "vehicle", "country": "DE"}
        )
        assert response.status_code == 200, f"CSV sample failed: {response.status_code} - {response.text}"
        assert "text/csv" in response.headers.get("content-type", ""), \
            f"Expected CSV content-type, got {response.headers.get('content-type')}"

    def test_xlsx_export_returns_403(self, auth_headers):
        """GET /api/admin/categories/import-export/export/xlsx should return 403 + feature_disabled"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/export/xlsx",
            headers=auth_headers,
            params={"module": "vehicle", "country": "DE"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected 'feature_disabled', got {data}"

    def test_xlsx_sample_returns_403(self, auth_headers):
        """GET /api/admin/categories/import-export/sample/xlsx should return 403 + feature_disabled"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/sample/xlsx",
            headers=auth_headers,
            params={"module": "vehicle", "country": "DE"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected 'feature_disabled', got {data}"


# ==== Dashboard Error Handling Test ====

class TestDashboardErrorHandling:
    """Dashboard should handle errors gracefully"""

    def test_dashboard_without_auth_returns_401(self):
        """Dashboard without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard/summary")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_dashboard_invalid_trend_days_returns_400(self, auth_headers):
        """Dashboard with invalid trend_days should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard/summary",
            headers=auth_headers,
            params={"trend_days": 1}  # Less than min (7)
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
