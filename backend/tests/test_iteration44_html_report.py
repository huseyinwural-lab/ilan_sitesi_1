"""
Iteration 44: HTML Report Endpoint & UI Button Tests
- GET /api/admin/ui/configs/dashboard/ops-alerts/html-report endpoint returns 200 + text/html
- HTML report query param channels filters (smtp, slack)
- Auth check: html-report endpoint returns 401/403 for unauthorized users
- Regression: Alert simulation flow not broken
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestHtmlReportEndpoint:
    """HTML Report endpoint tests"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token for tests"""
        # Admin login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.admin_token = login_response.json().get("access_token")
        self.admin_headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json",
        }

    def test_html_report_returns_200_and_text_html(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/html-report should return 200 + text/html"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/html-report",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected text/html content-type, got {content_type}"
        # Check HTML structure
        assert "<!doctype html>" in response.text.lower() or "<html" in response.text.lower(), "Response should contain HTML"
        print(f"PASS: HTML report returned 200 with text/html content-type, length={len(response.text)}")

    def test_html_report_channels_filter_smtp(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/html-report?channels=smtp should filter to SMTP only"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/html-report?channels=smtp",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected text/html, got {content_type}"
        # Verify HTML contains smtp channel info
        assert "smtp" in response.text.lower(), "HTML report should mention smtp channel"
        print("PASS: HTML report with channels=smtp filter returned 200")

    def test_html_report_channels_filter_slack(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/html-report?channels=slack should filter to Slack only"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/html-report?channels=slack",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected text/html, got {content_type}"
        assert "slack" in response.text.lower(), "HTML report should mention slack channel"
        print("PASS: HTML report with channels=slack filter returned 200")

    def test_html_report_channels_filter_combined(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/html-report?channels=smtp,slack should filter to both channels"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/html-report?channels=smtp,slack",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, f"Expected text/html, got {content_type}"
        print("PASS: HTML report with channels=smtp,slack combined filter returned 200")

    def test_html_report_unauthorized_no_token(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/html-report without auth should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/html-report",
            # No Authorization header
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print("PASS: HTML report without auth returns 401")

    def test_html_report_forbidden_non_admin(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/html-report with dealer token should return 403"""
        # Login as dealer
        dealer_login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer1772201722@example.com", "password": "Dealer123!"},
        )
        if dealer_login.status_code != 200:
            pytest.skip("Dealer login not available for testing")
        dealer_token = dealer_login.json().get("access_token")
        dealer_headers = {"Authorization": f"Bearer {dealer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/html-report",
            headers=dealer_headers,
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print("PASS: HTML report with dealer token returns 403")


class TestAlertSimulationRegression:
    """Regression tests to ensure alert simulation flow is not broken"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token for tests"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.admin_token = login_response.json().get("access_token")
        self.admin_headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json",
        }

    def test_secret_checklist_still_works(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/secret-checklist should still return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-checklist",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "channels" in data, "Response should contain channels"
        print("PASS: Secret checklist endpoint still works")

    def test_secret_presence_still_works(self):
        """GET /api/admin/ui/configs/dashboard/ops-alerts/secret-presence should still return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # Response is nested under ops_alerts_secret_presence
        assert "ops_alerts_secret_presence" in data, "Response should contain ops_alerts_secret_presence"
        presence_data = data["ops_alerts_secret_presence"]
        assert "status" in presence_data, "Presence data should contain status"
        print("PASS: Secret presence endpoint still works")

    def test_alert_delivery_metrics_still_works(self):
        """GET /api/admin/ops/alert-delivery-metrics should still return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=self.admin_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: Alert delivery metrics endpoint still works")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
