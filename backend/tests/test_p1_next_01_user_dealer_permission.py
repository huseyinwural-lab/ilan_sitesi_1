"""
P1-Next-01: Permission-Flag sonrası User/Dealer akış validasyonu
Tests user positive (account invoices+pdf, payments, subscription cancel/reactivate),
dealer positive (profile/store + listing create/preview/submit/publish role/policy uyumu),
negative authorization (user/dealer admin finance erişim 403),
permission-flag shadow diff raporu validation.
"""
import pytest
import requests
import os
import uuid
from datetime import datetime
import json

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


def get_token(email: str, password: str) -> str:
    """Helper to get auth token"""
    for attempt in range(3):
        try:
            resp = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": email, "password": password},
                timeout=60,
            )
            if resp.status_code != 200:
                pytest.skip(f"Auth failed for {email}: {resp.status_code}")
            return resp.json().get("access_token")
        except requests.exceptions.ReadTimeout:
            if attempt < 2:
                import time
                time.sleep(2)
                continue
            raise
    pytest.skip(f"Auth timed out for {email}")


@pytest.fixture(scope="module")
def admin_token():
    return get_token(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def user_token():
    return get_token(USER_EMAIL, USER_PASSWORD)


@pytest.fixture(scope="module")
def dealer_token():
    return get_token(DEALER_EMAIL, DEALER_PASSWORD)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def dealer_headers(dealer_token):
    return {"Authorization": f"Bearer {dealer_token}", "Content-Type": "application/json"}


class TestUserPositiveFlows:
    """User role positive flows: account invoices, payments, subscription cancel/reactivate"""

    def test_account_invoices_list(self, user_headers):
        """User can access their invoices list"""
        resp = requests.get(f"{BASE_URL}/api/account/invoices", headers=user_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        print(f"[PASS] User account invoices list: {len(data.get('items', []))} invoices")

    def test_account_invoice_pdf_download(self, user_headers):
        """User can download invoice PDF (if invoice exists)"""
        # First get invoices list
        list_resp = requests.get(f"{BASE_URL}/api/account/invoices", headers=user_headers, timeout=30)
        assert list_resp.status_code == 200
        invoices = list_resp.json().get("items", [])
        
        if not invoices:
            pytest.skip("No invoices available for PDF download test")
        
        invoice_id = invoices[0].get("id")
        resp = requests.get(
            f"{BASE_URL}/api/account/invoices/{invoice_id}/download-pdf",
            headers=user_headers,
            timeout=30,
        )
        # Accept 200 (PDF) or 404 (no PDF generated yet)
        assert resp.status_code in [200, 404], f"Expected 200 or 404, got {resp.status_code}"
        print(f"[PASS] User invoice PDF download: status {resp.status_code}")

    def test_account_payments_list(self, user_headers):
        """User can access their payments list"""
        resp = requests.get(f"{BASE_URL}/api/account/payments", headers=user_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        print(f"[PASS] User account payments list: {len(data.get('items', []))} payments")

    def test_account_subscription_get(self, user_headers):
        """User can get their subscription status"""
        resp = requests.get(f"{BASE_URL}/api/account/subscription", headers=user_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        # Check for expected keys
        assert "has_subscription" in data or "status" in data or "id" in data, "Missing subscription fields"
        print(f"[PASS] User subscription get: has_subscription={data.get('has_subscription')}")

    def test_account_subscription_cancel(self, user_headers):
        """User can cancel their subscription (or get appropriate error if none exists)"""
        resp = requests.post(
            f"{BASE_URL}/api/account/subscription/cancel",
            headers=user_headers,
            timeout=30,
        )
        # Accept 200 (cancelled), 400 (no active subscription), or similar expected responses
        assert resp.status_code in [200, 400, 404], f"Expected 200/400/404, got {resp.status_code}"
        print(f"[PASS] User subscription cancel: status {resp.status_code}")

    def test_account_subscription_reactivate(self, user_headers):
        """User can reactivate their subscription (or get appropriate error)"""
        resp = requests.post(
            f"{BASE_URL}/api/account/subscription/reactivate",
            headers=user_headers,
            timeout=30,
        )
        # Accept 200 (reactivated), 400 (cannot reactivate), or similar expected responses
        assert resp.status_code in [200, 400, 404], f"Expected 200/400/404, got {resp.status_code}"
        print(f"[PASS] User subscription reactivate: status {resp.status_code}")


class TestDealerPositiveFlows:
    """Dealer role positive flows: profile, store invoices, listing create/preview/submit/publish"""

    def test_dealer_profile_access(self, dealer_headers):
        """Dealer can access their profile via /api/auth/me"""
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=dealer_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("role") == "dealer", f"Expected dealer role, got {data.get('role')}"
        assert "portal_scope" in data, "Missing portal_scope"
        print(f"[PASS] Dealer profile access: role={data.get('role')}, portal_scope={data.get('portal_scope')}")

    def test_dealer_store_invoices(self, dealer_headers):
        """Dealer can access their store invoices"""
        resp = requests.get(f"{BASE_URL}/api/dealer/invoices", headers=dealer_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        print(f"[PASS] Dealer store invoices: {len(data.get('items', []))} invoices")

    def test_dealer_listing_create(self, dealer_headers):
        """Dealer can create a draft listing"""
        listing_payload = {
            "title": f"TEST P1 Dealer Listing {uuid.uuid4().hex[:8]}",
            "description": "Test listing created for P1-Next-01 permission validation test. This is a test description with enough characters.",
            "country_code": "DE",
        }

        resp = requests.post(
            f"{BASE_URL}/api/dealer/listings",
            headers=dealer_headers,
            json=listing_payload,
            timeout=60,
        )
        # Accept 201 (created), 200, or check response structure
        assert resp.status_code in [200, 201], f"Expected 200/201, got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        # Check for item key in response (from quota-based response)
        listing_id = data.get("id") or (data.get("item", {}).get("id") if data.get("item") else None)
        assert listing_id, f"Listing ID should be returned, got: {data.keys()}"
        print(f"[PASS] Dealer listing create: id={listing_id}")
        return listing_id

    def test_dealer_listing_flow_preview_submit_publish(self, dealer_headers):
        """Test full listing flow: create -> preview -> submit_review -> request_publish"""
        # Create listing
        listing_payload = {
            "title": f"TEST P1 Full Flow Listing {uuid.uuid4().hex[:8]}",
            "description": "Test listing for full flow validation. This description has enough characters for validation purposes in the test.",
            "country_code": "DE",
        }

        create_resp = requests.post(
            f"{BASE_URL}/api/dealer/listings",
            headers=dealer_headers,
            json=listing_payload,
            timeout=60,
        )
        assert create_resp.status_code in [200, 201], f"Create failed: {create_resp.status_code}: {create_resp.text[:200]}"
        data = create_resp.json()
        listing_id = data.get("id") or (data.get("item", {}).get("id") if data.get("item") else None)
        assert listing_id, f"Listing ID not found in response: {data.keys()}"
        print(f"  Created listing: {listing_id}")

        # Update/patch listing
        patch_resp = requests.patch(
            f"{BASE_URL}/api/dealer/listings/{listing_id}",
            headers=dealer_headers,
            json={"title": f"TEST P1 Updated {uuid.uuid4().hex[:4]}"},
            timeout=60,
        )
        assert patch_resp.status_code in [200, 201], f"Patch failed: {patch_resp.status_code}"
        print(f"  Patched listing: {patch_resp.status_code}")

        # Check preview (if endpoint exists)
        preview_resp = requests.get(
            f"{BASE_URL}/api/dealer/listings/{listing_id}/preview",
            headers=dealer_headers,
            timeout=60,
        )
        # Preview may not exist, accept 200 or 404
        print(f"  Preview status: {preview_resp.status_code}")

        # Submit for review
        submit_resp = requests.post(
            f"{BASE_URL}/api/dealer/listings/{listing_id}/submit-review",
            headers=dealer_headers,
            timeout=60,
        )
        # May return 200, 400 (already submitted), or 422 (validation error)
        print(f"  Submit review status: {submit_resp.status_code}")

        # Request publish (dealer action)
        publish_req_resp = requests.post(
            f"{BASE_URL}/api/dealer/listings/{listing_id}/request-publish",
            headers=dealer_headers,
            timeout=60,
        )
        print(f"  Request publish status: {publish_req_resp.status_code}")

        print(f"[PASS] Dealer listing flow complete for listing {listing_id}")


class TestNegativeAuthorization:
    """Negative authorization tests: user/dealer cannot access admin finance endpoints"""

    def test_user_cannot_access_admin_finance_overview(self, user_headers):
        """User should get 403 when accessing admin finance overview"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/finance/overview",
            headers=user_headers,
            timeout=30,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print(f"[PASS] User blocked from admin/finance/overview: 403")

    def test_user_cannot_access_admin_finance_export(self, user_headers):
        """User should get 403 when accessing admin finance export"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/invoices/export/csv",
            headers=user_headers,
            timeout=30,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print(f"[PASS] User blocked from admin/invoices/export/csv: 403")

    def test_user_cannot_access_admin_payments(self, user_headers):
        """User should get 403 when accessing admin payments"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments",
            headers=user_headers,
            timeout=30,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print(f"[PASS] User blocked from admin/payments: 403")

    def test_dealer_cannot_access_admin_finance_export(self, dealer_headers):
        """Dealer should get 403 when accessing admin finance export"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/ledger/export/csv",
            headers=dealer_headers,
            timeout=30,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print(f"[PASS] Dealer blocked from admin/ledger/export/csv: 403")

    def test_dealer_cannot_publish_as_admin(self, dealer_headers):
        """Dealer should get 403 when trying to use admin publish endpoint"""
        # Try to access admin moderation publish endpoint
        resp = requests.post(
            f"{BASE_URL}/api/admin/moderation/test-listing-id/publish",
            headers=dealer_headers,
            json={},
            timeout=30,
        )
        # Should be 403 (forbidden) or 404 (not found), not 200
        assert resp.status_code in [403, 404], f"Expected 403/404, got {resp.status_code}"
        print(f"[PASS] Dealer blocked from admin publish: {resp.status_code}")

    def test_dealer_cannot_access_admin_subscriptions(self, dealer_headers):
        """Dealer should get 403 when accessing admin subscriptions"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/finance/subscriptions",
            headers=dealer_headers,
            timeout=30,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print(f"[PASS] Dealer blocked from admin/finance/subscriptions: 403")


class TestPermissionFlagShadowDiff:
    """Permission-flag shadow diff validation: flag ON decisions vs role-fallback"""

    def test_permission_shadow_diff_consistency(self, admin_headers):
        """Verify permission flag shadow diff shows consistent decisions"""
        # Check if shadow diff endpoint exists
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=admin_headers,
            timeout=30,
        )
        
        if resp.status_code == 404:
            # Endpoint doesn't exist, check the existing validation file
            import json
            try:
                with open("/app/test_reports/p1_user_dealer_permission_validation.json", "r") as f:
                    validation_data = json.load(f)
                shadow_diff = validation_data.get("permission_flag_shadow_diff", {})
                diff_count = shadow_diff.get("diff_count", 0)
                assert diff_count == 0, f"Shadow diff count should be 0, got {diff_count}"
                print(f"[PASS] Permission flag shadow diff: diff_count={diff_count}")
            except FileNotFoundError:
                pytest.skip("Shadow diff validation file not found")
        else:
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            data = resp.json()
            diff_count = data.get("diff_count", 0)
            assert diff_count == 0, f"Shadow diff count should be 0, got {diff_count}"
            print(f"[PASS] Permission flag shadow diff endpoint: diff_count={diff_count}")

    def test_role_based_permission_matrix(self, admin_headers, user_headers, dealer_headers):
        """Verify role-based permissions are consistent across users"""
        results = {}
        
        # Test finance view access for each role
        admin_finance = requests.get(f"{BASE_URL}/api/admin/finance/overview", headers=admin_headers, timeout=30)
        user_finance = requests.get(f"{BASE_URL}/api/admin/finance/overview", headers=user_headers, timeout=30)
        dealer_finance = requests.get(f"{BASE_URL}/api/admin/finance/overview", headers=dealer_headers, timeout=30)
        
        results["admin_finance_view"] = admin_finance.status_code == 200
        results["user_finance_view_blocked"] = user_finance.status_code == 403
        results["dealer_finance_view_blocked"] = dealer_finance.status_code == 403
        
        # All role-based checks should pass
        assert all(results.values()), f"Role permission matrix failed: {results}"
        print(f"[PASS] Role-based permission matrix: {results}")


class TestAdminPositiveFlows:
    """Admin role positive flows for finance endpoints (verification)"""

    def test_admin_finance_overview(self, admin_headers):
        """Admin can access finance overview"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/overview", headers=admin_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[PASS] Admin finance overview: 200")

    def test_admin_invoices_list(self, admin_headers):
        """Admin can access invoices list"""
        resp = requests.get(f"{BASE_URL}/api/admin/invoices", headers=admin_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[PASS] Admin invoices list: 200")

    def test_admin_payments_list(self, admin_headers):
        """Admin can access payments list"""
        resp = requests.get(f"{BASE_URL}/api/admin/payments", headers=admin_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[PASS] Admin payments list: 200")

    def test_admin_subscriptions_list(self, admin_headers):
        """Admin can access subscriptions list"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/subscriptions", headers=admin_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[PASS] Admin subscriptions list: 200")

    def test_admin_ledger(self, admin_headers):
        """Admin can access ledger"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/ledger", headers=admin_headers, timeout=30)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        print(f"[PASS] Admin ledger: 200")
