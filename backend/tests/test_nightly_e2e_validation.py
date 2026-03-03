"""
Nightly E2E Extended Validation Tests
- Validates report file structure and content
- Smoke tests for user/dealer/admin critical endpoints
"""
import json
import os
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
REPORT_PATH = Path("/app/test_reports/nightly_e2e_extended.json")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin login failed")


@pytest.fixture(scope="module")
def user_token(api_client):
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("User login failed")


@pytest.fixture(scope="module")
def dealer_token(api_client):
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEALER_EMAIL,
        "password": DEALER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Dealer login failed")


class TestNightlyReportStructure:
    """Tests for nightly_e2e_extended.json report structure"""

    def test_report_file_exists(self):
        """Verify report file exists"""
        assert REPORT_PATH.exists(), f"Report file not found: {REPORT_PATH}"

    def test_report_is_valid_json(self):
        """Verify report is valid JSON"""
        content = REPORT_PATH.read_text(encoding="utf-8")
        data = json.loads(content)
        assert isinstance(data, dict), "Report should be a dict"

    def test_report_has_artifact_requirements(self):
        """Verify artifact_requirements field with broken_flows and endpoint_http_4xx_5xx"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        assert "artifact_requirements" in data, "Missing artifact_requirements"
        ar = data["artifact_requirements"]
        assert "broken_flows" in ar, "Missing broken_flows in artifact_requirements"
        assert "endpoint_http_4xx_5xx" in ar, "Missing endpoint_http_4xx_5xx in artifact_requirements"
        assert isinstance(ar["broken_flows"], list), "broken_flows should be a list"
        assert isinstance(ar["endpoint_http_4xx_5xx"], list), "endpoint_http_4xx_5xx should be a list"

    def test_report_has_ci_gate(self):
        """Verify ci_gate field with finance/listing merge block logic"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        assert "ci_gate" in data, "Missing ci_gate"
        cg = data["ci_gate"]
        assert "merge_blocked" in cg, "Missing merge_blocked in ci_gate"
        assert "finance_gate" in cg, "Missing finance_gate in ci_gate"
        assert "listing_gate" in cg, "Missing listing_gate in ci_gate"
        assert isinstance(cg["merge_blocked"], bool), "merge_blocked should be bool"
        assert isinstance(cg["finance_gate"], bool), "finance_gate should be bool"
        assert isinstance(cg["listing_gate"], bool), "listing_gate should be bool"

    def test_report_has_latest_status(self):
        """Verify latest run status is PASS or FAIL"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        assert "latest" in data, "Missing latest"
        assert "status" in data["latest"], "Missing status in latest"
        assert data["latest"]["status"] in ["PASS", "FAIL"], "Invalid status value"

    def test_report_has_flows(self):
        """Verify flows contain user, dealer, admin"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        flows = data.get("latest", {}).get("flows", {})
        assert "user" in flows, "Missing user flow"
        assert "dealer" in flows, "Missing dealer flow"
        assert "admin" in flows, "Missing admin flow"


class TestUserCriticalEndpoints:
    """Smoke tests for user critical endpoints from nightly report"""

    def test_user_login(self, api_client):
        """User can login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_user_account_invoices(self, api_client, user_token):
        """User can list account invoices"""
        response = api_client.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200

    def test_user_subscription_cancel(self, api_client, user_token):
        """User can cancel subscription"""
        response = api_client.post(
            f"{BASE_URL}/api/account/subscription/cancel",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200

    def test_user_subscription_reactivate(self, api_client, user_token):
        """User can reactivate subscription"""
        response = api_client.post(
            f"{BASE_URL}/api/account/subscription/reactivate",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200


class TestDealerCriticalEndpoints:
    """Smoke tests for dealer critical endpoints from nightly report"""

    def test_dealer_login(self, api_client):
        """Dealer can login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_dealer_categories(self, api_client, dealer_token):
        """Dealer can get vehicle categories"""
        response = api_client.get(
            f"{BASE_URL}/api/categories/children?module=vehicle&country=DE",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200


class TestAdminCriticalEndpoints:
    """Smoke tests for admin critical endpoints from nightly report"""

    def test_admin_login(self, api_client):
        """Admin can login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_admin_finance_export_csv(self, api_client, admin_token):
        """Admin can export finance CSV"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/payments/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=120
        )
        assert response.status_code == 200

    def test_admin_me(self, api_client, admin_token):
        """Admin can get profile"""
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


class TestCIGateLogic:
    """Tests for CI gate merge block logic"""

    def test_ci_gate_consistency(self):
        """Verify CI gate logic: merge_blocked = NOT(finance_pass AND listing_pass)"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        latest = data.get("latest", {})
        ci_gate = data.get("ci_gate", {})

        finance_pass = latest.get("finance_e2e_pass", False)
        listing_pass = latest.get("listing_e2e_pass", False)
        merge_blocked = ci_gate.get("merge_blocked", True)

        expected_blocked = not (finance_pass and listing_pass)
        assert merge_blocked == expected_blocked, \
            f"CI gate logic mismatch: finance={finance_pass}, listing={listing_pass}, blocked={merge_blocked}"

    def test_finance_gate_logic(self):
        """Verify finance_gate = NOT(finance_e2e_pass)"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        latest = data.get("latest", {})
        ci_gate = data.get("ci_gate", {})

        finance_pass = latest.get("finance_e2e_pass", False)
        finance_gate = ci_gate.get("finance_gate", True)

        assert finance_gate == (not finance_pass), \
            f"finance_gate logic mismatch: pass={finance_pass}, gate={finance_gate}"

    def test_listing_gate_logic(self):
        """Verify listing_gate = NOT(listing_e2e_pass)"""
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        latest = data.get("latest", {})
        ci_gate = data.get("ci_gate", {})

        listing_pass = latest.get("listing_e2e_pass", False)
        listing_gate = ci_gate.get("listing_gate", True)

        assert listing_gate == (not listing_pass), \
            f"listing_gate logic mismatch: pass={listing_pass}, gate={listing_gate}"
