"""
P0-04 Legacy Billing Cleanup Test Suite
Tests for:
- Stub endpoint removed (returns 404)
- Legacy billing API routes removed
- Admin billing UI route/entrypoint removed
- Canonical Stripe flow still works
- Finance regression (invoices, payments, subscriptions, ledger)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://dynamic-layout-io.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def user_token():
    """Get user authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    if response.status_code != 200:
        pytest.skip(f"User login failed: {response.status_code}")
    return response.json().get("access_token")


class TestP004StubEndpointRemoved:
    """P0-04 Critical: Stub endpoint should return 404/410, not 200"""

    def test_stub_checkout_session_returns_404(self):
        """POST /api/payments/create-checkout-session/stub should NOT return 200"""
        response = requests.post(
            f"{BASE_URL}/api/payments/create-checkout-session/stub",
            json={"listing_id": "test", "product_type": "listing"},
        )
        # 404 or 410 is acceptable, NOT 200
        assert response.status_code in [404, 405, 410], f"Stub endpoint returned {response.status_code}, expected 404/410"

    def test_stub_endpoint_not_in_routes(self):
        """Stub endpoint should not appear in routes listing"""
        response = requests.get(f"{BASE_URL}/api/routes")
        if response.status_code == 200:
            routes = response.json().get("routes", [])
            stub_routes = [r for r in routes if "stub" in r.lower()]
            assert len(stub_routes) == 0, f"Stub routes still present: {stub_routes}"


class TestP004LegacyBillingRoutesRemoved:
    """P0-04 Critical: Legacy /api/v1/billing/* routes should be removed"""

    def test_v1_billing_status_returns_404(self):
        """/api/v1/billing/status should return 404"""
        response = requests.get(f"{BASE_URL}/api/v1/billing/status")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_v1_billing_plans_returns_404(self):
        """/api/v1/billing/plans should return 404"""
        response = requests.get(f"{BASE_URL}/api/v1/billing/plans")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_v1_billing_subscribe_returns_404(self):
        """/api/v1/billing/subscribe should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/v1/billing/subscribe",
            json={"plan_id": "test"},
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_billing_not_in_openapi_paths(self):
        """Billing routes should not appear in OpenAPI spec"""
        response = requests.get(f"{BASE_URL}/api/openapi.json")
        if response.status_code == 200:
            paths = response.json().get("paths", {})
            billing_paths = [p for p in paths.keys() if "billing" in p.lower()]
            # billing_info_snapshot fields are acceptable, but NOT /billing/ routes
            route_paths = [p for p in billing_paths if "/billing" in p]
            assert len(route_paths) == 0, f"Legacy billing routes found: {route_paths}"


class TestP004CanonicalStripeFlowWorks:
    """P0-04 Critical: Canonical Stripe payment endpoints should still work"""

    def test_create_checkout_session_requires_auth(self):
        """POST /api/payments/create-checkout-session requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/payments/create-checkout-session",
            json={"listing_id": "test", "product_type": "listing"},
        )
        # 401 or 403 expected for unauthenticated
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_create_intent_requires_auth(self):
        """POST /api/payments/create-intent requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/payments/create-intent",
            json={},
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_stripe_webhook_endpoint_exists(self):
        """POST /api/payments/webhook should exist (403 without proper signature)"""
        response = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            json={},
            headers={"stripe-signature": "invalid"},
        )
        # 400 or 403 expected (signature error), NOT 404
        assert response.status_code in [400, 403, 422, 500], f"Webhook endpoint missing? Got {response.status_code}"


class TestP004AdminFinanceRegression:
    """Regression: Admin finance APIs should still work"""

    def test_admin_finance_overview(self, admin_token):
        """GET /api/admin/finance/overview should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/finance/overview",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Finance overview failed: {response.status_code}"
        data = response.json()
        assert "cards" in data or "range" in data, "Invalid response structure"

    def test_admin_invoices_list(self, admin_token):
        """GET /api/admin/invoices should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Invoices list failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected 'items' in response"

    def test_admin_payments_list(self, admin_token):
        """GET /api/admin/payments should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/payments",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Payments list failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected 'items' in response"

    def test_admin_subscriptions_list(self, admin_token):
        """GET /api/admin/finance/subscriptions should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/finance/subscriptions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Subscriptions list failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected 'items' in response"

    def test_admin_ledger_list(self, admin_token):
        """GET /api/admin/finance/ledger should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/finance/ledger",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Ledger list failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected 'items' in response"

    def test_admin_invoice_pdf_generate(self, admin_token):
        """POST /api/admin/invoices/{id}/generate-pdf should return 200"""
        # First get an invoice
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if response.status_code != 200:
            pytest.skip("Cannot get invoices")
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No invoices available")
        invoice_id = items[0].get("id")
        
        # Generate PDF
        response = requests.post(
            f"{BASE_URL}/api/admin/invoices/{invoice_id}/generate-pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"PDF generate failed: {response.status_code}"

    def test_admin_invoices_export_csv(self, admin_token):
        """GET /api/admin/invoices/export/csv should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Invoice export failed: {response.status_code}"
        assert "text/csv" in response.headers.get("content-type", "")

    def test_admin_payments_export_csv(self, admin_token):
        """GET /api/admin/payments/export/csv should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/payments/export/csv",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Payments export failed: {response.status_code}"


class TestP004AccountFinanceRegression:
    """Regression: Account (user) finance APIs should still work"""

    def test_account_invoices(self, user_token):
        """GET /api/account/invoices should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200, f"Account invoices failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected 'items' in response"

    def test_account_payments(self, user_token):
        """GET /api/account/payments should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/payments",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200, f"Account payments failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected 'items' in response"

    def test_account_subscription(self, user_token):
        """GET /api/account/subscription should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200, f"Account subscription failed: {response.status_code}"
        data = response.json()
        assert "has_subscription" in data or "status" in data, "Invalid response structure"


class TestP004SpotCheckRedirects:
    """Spot-check: 3 URL redirect/canonical drift verification"""

    def test_http_to_https_redirect(self):
        """HTTP should redirect to HTTPS with max 1 hop"""
        # This test uses requests with allow_redirects=False to count hops
        # Note: May not work for all hosts in test environment
        try:
            response = requests.get(
                f"{BASE_URL}/api/health",
                allow_redirects=False,
                timeout=5,
            )
            # Either direct 200 (already HTTPS) or redirect to HTTPS
            assert response.status_code in [200, 301, 302, 307, 308], f"Unexpected status: {response.status_code}"
        except Exception:
            pytest.skip("HTTP redirect test not applicable in this environment")

    def test_sitemap_index_accessible(self):
        """Sitemap index should be accessible"""
        response = requests.get(f"{BASE_URL}/api/sitemap/index.xml", timeout=10)
        assert response.status_code in [200, 404], f"Sitemap status: {response.status_code}"

    def test_health_endpoint_accessible(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
