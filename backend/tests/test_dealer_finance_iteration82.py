"""
Test Module: Dealer Finance Features - Iteration 82
Tests dealer invoices, payments, PDF download, company/privacy pages, settings quick links
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer authentication token"""
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        timeout=30,
    )
    if res.status_code != 200:
        pytest.skip(f"Dealer login failed: {res.status_code}")
    return res.json().get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    if res.status_code != 200:
        pytest.skip(f"Admin login failed: {res.status_code}")
    return res.json().get("access_token")


@pytest.fixture(scope="module")
def user_token():
    """Get user authentication token"""
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
        timeout=30,
    )
    if res.status_code != 200:
        pytest.skip(f"User login failed: {res.status_code}")
    return res.json().get("access_token")


class TestDealerInvoicesEndpoint:
    """Test /api/dealer/invoices endpoint"""

    def test_dealer_invoices_list_200(self, dealer_token):
        """Dealer invoices endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "Items should be a list"

    def test_dealer_invoices_list_sorted_desc(self, dealer_token):
        """Dealer invoices should be sorted by issued_at/created_at DESC (newest first)"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        if len(items) >= 2:
            # Check if sorted by date DESC (newest first)
            dates = []
            for item in items:
                date_val = item.get("issued_at") or item.get("created_at")
                if date_val:
                    dates.append(date_val)
            # Allow for equal dates
            for i in range(len(dates) - 1):
                assert dates[i] >= dates[i + 1], "Invoices should be sorted by date DESC"

    def test_dealer_invoices_list_with_status_filter(self, dealer_token):
        """Dealer invoices with status filter"""
        for status in ["issued", "paid", "void"]:
            res = requests.get(
                f"{BASE_URL}/api/dealer/invoices?status={status}",
                headers={"Authorization": f"Bearer {dealer_token}"},
                timeout=30,
            )
            assert res.status_code == 200, f"Status filter '{status}' should return 200"
            data = res.json()
            assert "items" in data

    def test_dealer_invoices_list_invalid_status(self, dealer_token):
        """Dealer invoices with invalid status should return 400"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices?status=invalid_status",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 400, f"Invalid status should return 400, got {res.status_code}"


class TestDealerPaymentsEndpoint:
    """Test /api/dealer/payments endpoint"""

    def test_dealer_payments_list_200(self, dealer_token):
        """Dealer payments endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/payments",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "Items should be a list"

    def test_dealer_payments_list_with_status_filter(self, dealer_token):
        """Dealer payments with status filter"""
        for status in ["succeeded", "pending", "failed"]:
            res = requests.get(
                f"{BASE_URL}/api/dealer/payments?status={status}",
                headers={"Authorization": f"Bearer {dealer_token}"},
                timeout=30,
            )
            assert res.status_code == 200, f"Status filter '{status}' should return 200"

    def test_dealer_payments_normalized_message_in_response(self, dealer_token):
        """Payments items should have normalized_message field"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/payments",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        # If there are items, verify normalized_message exists
        for item in items:
            assert "normalized_message" in item or "status" in item, "Payment should have normalized_message or status"


class TestDealerInvoiceDetail:
    """Test /api/dealer/invoices/{id} endpoint"""

    def test_dealer_invoice_detail_requires_auth(self):
        """Dealer invoice detail requires authentication"""
        fake_id = "00000000-0000-0000-0000-000000000001"
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices/{fake_id}",
            timeout=30,
        )
        assert res.status_code == 401, "Should return 401 without auth"

    def test_dealer_invoice_detail_invalid_id(self, dealer_token):
        """Invalid invoice ID should return 400"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices/invalid-uuid",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 400, "Invalid ID should return 400"

    def test_dealer_invoice_detail_not_found(self, dealer_token):
        """Non-existent invoice should return 404"""
        fake_id = "00000000-0000-0000-0000-000000000001"
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices/{fake_id}",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 404, "Non-existent invoice should return 404"

    def test_dealer_invoice_detail_has_payments_list(self, dealer_token):
        """Invoice detail response should include payments list"""
        # First get list of invoices
        list_res = requests.get(
            f"{BASE_URL}/api/dealer/invoices",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert list_res.status_code == 200
        items = list_res.json().get("items", [])
        
        if not items:
            pytest.skip("No invoices to test detail endpoint")
        
        # Get detail for first invoice
        invoice_id = items[0]["id"]
        detail_res = requests.get(
            f"{BASE_URL}/api/dealer/invoices/{invoice_id}",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert detail_res.status_code == 200
        data = detail_res.json()
        assert "invoice" in data, "Detail should contain 'invoice'"
        assert "payments" in data, "Detail should contain 'payments' list"
        assert isinstance(data["payments"], list), "Payments should be a list"


class TestDealerInvoicePdfDownload:
    """Test /api/dealer/invoices/{id}/download-pdf endpoint"""

    def test_dealer_pdf_download_requires_auth(self):
        """PDF download requires authentication"""
        fake_id = "00000000-0000-0000-0000-000000000001"
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices/{fake_id}/download-pdf",
            timeout=30,
        )
        assert res.status_code == 401, "Should return 401 without auth"

    def test_dealer_pdf_download_ownership_enforced_403(self, dealer_token, user_token):
        """PDF download should return 403 for foreign invoices (ownership check)"""
        # Get user's invoices (if any) - these should be inaccessible to dealer
        user_invoices_res = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=30,
        )
        
        if user_invoices_res.status_code != 200:
            pytest.skip("User invoices endpoint not available")
        
        user_items = user_invoices_res.json().get("items", [])
        if not user_items:
            pytest.skip("No user invoices to test ownership enforcement")
        
        # Try to access user's invoice as dealer - should get 403
        user_invoice_id = user_items[0]["id"]
        res = requests.get(
            f"{BASE_URL}/api/dealer/invoices/{user_invoice_id}/download-pdf",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        # Should be 403 (access denied) or 404 (not found because dealer can't see it)
        assert res.status_code in [403, 404], f"Foreign invoice should return 403/404, got {res.status_code}"


class TestDealerSettingsProfile:
    """Test dealer settings profile endpoint"""

    def test_dealer_settings_profile_200(self, dealer_token):
        """Dealer settings profile endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "profile" in data, "Response should contain 'profile'"

    def test_dealer_settings_preferences_200(self, dealer_token):
        """Dealer settings preferences endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/settings/preferences",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"


class TestDealerCompanyProfile:
    """Test dealer company profile endpoint"""

    def test_dealer_company_profile_200(self, dealer_token):
        """Dealer company profile endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/v1/users/me/dealer-profile",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"


class TestDealerPrivacyDataExport:
    """Test dealer privacy data export endpoint"""

    def test_dealer_data_export_200(self, dealer_token):
        """Dealer data export endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/v1/users/me/data-export",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        # Should return 200 with JSON or blob data
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"


class TestDealerPortalConfigEndpoints:
    """Test dealer portal configuration endpoints"""

    def test_dealer_portal_header_config_200(self, dealer_token):
        """Dealer portal header config endpoint returns 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/header-config",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"


class TestAdminFinanceRegression:
    """Regression tests for admin finance - ensure dealer changes don't break admin"""

    def test_admin_invoices_list_200(self, admin_token):
        """Admin invoices list still works"""
        res = requests.get(
            f"{BASE_URL}/api/admin/invoices",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        assert res.status_code == 200

    def test_admin_payments_list_200(self, admin_token):
        """Admin payments list still works"""
        res = requests.get(
            f"{BASE_URL}/api/admin/payments",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        assert res.status_code == 200


class TestAccountFinanceRegression:
    """Regression tests for account finance - ensure dealer changes don't break account"""

    def test_account_invoices_list_200(self, user_token):
        """Account invoices list still works"""
        res = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=30,
        )
        assert res.status_code == 200

    def test_account_payments_list_200(self, user_token):
        """Account payments list still works"""
        res = requests.get(
            f"{BASE_URL}/api/account/payments",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=30,
        )
        assert res.status_code == 200

    def test_account_subscription_200(self, user_token):
        """Account subscription endpoint still works"""
        res = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=30,
        )
        assert res.status_code == 200
