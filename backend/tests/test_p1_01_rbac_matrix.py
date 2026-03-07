"""
P1-01 RBAC Matrix Test Suite
Tests role-based access control for:
- Finance view/edit/export permissions
- Content publish permissions
- Negative authorization tests (403)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://builder-hub-151.preview.emergentagent.com')
API = f"{BASE_URL}/api"

# Test credentials - expected seed data
CREDENTIALS = {
    "super_admin": {"email": "admin@platform.com", "password": "Admin123!"},
    "country_admin": {"email": "countryadmin@platform.com", "password": "Country123!"},
    "admin": {"email": "admin_view@platform.com", "password": "AdminView123!"},
    "dealer": {"email": "dealer@platform.com", "password": "Dealer123!"},
    "user": {"email": "user@platform.com", "password": "User123!"},
}

# Cache for tokens
_token_cache = {}


def get_token(role: str) -> str:
    """Get auth token for a specific role"""
    if role in _token_cache:
        return _token_cache[role]
    
    creds = CREDENTIALS.get(role)
    if not creds:
        pytest.skip(f"No credentials for role: {role}")
    
    resp = requests.post(f"{API}/auth/login", json={
        "email": creds["email"],
        "password": creds["password"]
    })
    
    if resp.status_code != 200:
        pytest.skip(f"Login failed for {role}: {resp.status_code} - {resp.text}")
    
    token = resp.json().get("access_token")
    _token_cache[role] = token
    return token


def auth_header(role: str) -> dict:
    """Get auth header for a specific role"""
    return {"Authorization": f"Bearer {get_token(role)}"}


class TestRoleInventory:
    """Test that all expected roles can login successfully"""
    
    def test_super_admin_login(self):
        """super_admin: admin@platform.com"""
        resp = requests.post(f"{API}/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert resp.status_code == 200, f"super_admin login failed: {resp.text}"
        data = resp.json()
        assert data.get("user", {}).get("role") == "super_admin"
        print("✓ super_admin login OK")
    
    def test_country_admin_login(self):
        """country_admin: countryadmin@platform.com"""
        resp = requests.post(f"{API}/auth/login", json={
            "email": "countryadmin@platform.com",
            "password": "Country123!"
        })
        assert resp.status_code == 200, f"country_admin login failed: {resp.text}"
        data = resp.json()
        assert data.get("user", {}).get("role") == "country_admin"
        print("✓ country_admin login OK")
    
    def test_dealer_login(self):
        """dealer: dealer@platform.com"""
        resp = requests.post(f"{API}/auth/login", json={
            "email": "dealer@platform.com",
            "password": "Dealer123!"
        })
        assert resp.status_code == 200, f"dealer login failed: {resp.text}"
        data = resp.json()
        assert data.get("user", {}).get("role") == "dealer"
        print("✓ dealer login OK")
    
    def test_user_login(self):
        """user (individual): user@platform.com"""
        resp = requests.post(f"{API}/auth/login", json={
            "email": "user@platform.com",
            "password": "User123!"
        })
        assert resp.status_code == 200, f"user login failed: {resp.text}"
        data = resp.json()
        assert data.get("user", {}).get("role") in ("individual", "user")
        print("✓ user login OK")


class TestFinanceViewPermissions:
    """
    Finance view endpoints should be accessible by:
    - super_admin: global view
    - country_admin: scoped view
    - admin: view-only
    """
    
    def test_super_admin_can_view_invoices(self):
        """super_admin can view invoices (global)"""
        resp = requests.get(f"{API}/admin/invoices?country=DE", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin invoices view failed: {resp.text}"
        print("✓ super_admin can view invoices")
    
    def test_country_admin_can_view_invoices(self):
        """country_admin can view invoices (scoped to country)"""
        resp = requests.get(f"{API}/admin/invoices?country=DE", headers=auth_header("country_admin"))
        assert resp.status_code == 200, f"country_admin invoices view failed: {resp.text}"
        print("✓ country_admin can view invoices (scoped)")
    
    def test_super_admin_can_view_plans(self):
        """super_admin can view plans"""
        resp = requests.get(f"{API}/admin/plans", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin plans view failed: {resp.text}"
        print("✓ super_admin can view plans")
    
    def test_country_admin_can_view_plans(self):
        """country_admin can view plans (scoped)"""
        resp = requests.get(f"{API}/admin/plans?scope=country&country_code=DE", headers=auth_header("country_admin"))
        assert resp.status_code == 200, f"country_admin plans view failed: {resp.text}"
        print("✓ country_admin can view plans (scoped)")
    
    def test_super_admin_can_view_tax_rates(self):
        """super_admin can view tax rates"""
        resp = requests.get(f"{API}/admin/tax-rates?country=DE", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin tax-rates view failed: {resp.text}"
        print("✓ super_admin can view tax-rates")
    
    def test_country_admin_can_view_tax_rates(self):
        """country_admin can view tax rates (scoped)"""
        resp = requests.get(f"{API}/admin/tax-rates?country=DE", headers=auth_header("country_admin"))
        assert resp.status_code == 200, f"country_admin tax-rates view failed: {resp.text}"
        print("✓ country_admin can view tax-rates (scoped)")
    
    def test_super_admin_can_view_payments(self):
        """super_admin can view payments/transactions"""
        resp = requests.get(f"{API}/admin/payments", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin payments view failed: {resp.text}"
        print("✓ super_admin can view payments")
    
    def test_super_admin_can_view_finance_overview(self):
        """super_admin can view finance overview"""
        resp = requests.get(f"{API}/admin/finance/overview", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin finance overview failed: {resp.text}"
        print("✓ super_admin can view finance overview")


class TestFinanceExportPermissions:
    """
    Finance export endpoints should be accessible by:
    - super_admin: yes
    - country_admin: yes (scoped)
    - admin: NO (403)
    - dealer/user: NO (403)
    """
    
    def test_super_admin_can_export_payments(self):
        """super_admin can export payments CSV"""
        resp = requests.get(f"{API}/admin/payments/export/csv", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin payments export failed: {resp.status_code}"
        assert "text/csv" in resp.headers.get("content-type", ""), "Expected CSV response"
        print("✓ super_admin can export payments CSV")
    
    def test_country_admin_can_export_payments(self):
        """country_admin can export payments CSV (scoped)"""
        resp = requests.get(f"{API}/admin/payments/export/csv", headers=auth_header("country_admin"))
        assert resp.status_code == 200, f"country_admin payments export failed: {resp.status_code}"
        print("✓ country_admin can export payments CSV (scoped)")
    
    def test_super_admin_can_export_invoices(self):
        """super_admin can export invoices CSV"""
        resp = requests.get(f"{API}/admin/invoices/export/csv", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin invoices export failed: {resp.status_code}"
        print("✓ super_admin can export invoices CSV")
    
    def test_country_admin_can_export_invoices(self):
        """country_admin can export invoices CSV (scoped)"""
        resp = requests.get(f"{API}/admin/invoices/export/csv", headers=auth_header("country_admin"))
        assert resp.status_code == 200, f"country_admin invoices export failed: {resp.status_code}"
        print("✓ country_admin can export invoices CSV (scoped)")
    
    def test_super_admin_can_export_ledger(self):
        """super_admin can export ledger CSV"""
        resp = requests.get(f"{API}/admin/ledger/export/csv", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin ledger export failed: {resp.status_code}"
        print("✓ super_admin can export ledger CSV")


class TestFinanceEditPermissions:
    """
    Finance edit endpoints should only be accessible by:
    - super_admin: yes
    - country_admin: NO (403)
    - admin: NO (403)
    """
    
    def test_super_admin_can_create_plan(self):
        """super_admin can create plan"""
        resp = requests.post(f"{API}/admin/plans", 
            headers=auth_header("super_admin"),
            json={
                "name": "TEST_RBAC_Plan",
                "slug": "test-rbac-plan",
                "country_scope": "global",
                "period": "monthly",
                "price_amount": 99,
                "listing_quota": 10,
                "showcase_quota": 5,
                "active_flag": False
            })
        # May succeed or return 409 if exists - both are acceptable (proves permission)
        assert resp.status_code in (200, 201, 409), f"super_admin plan create unexpected: {resp.status_code} - {resp.text}"
        print(f"✓ super_admin can create plan (status={resp.status_code})")
    
    def test_super_admin_can_create_tax_rate(self):
        """super_admin can create tax rate"""
        resp = requests.post(f"{API}/admin/tax-rates",
            headers=auth_header("super_admin"),
            json={
                "country_code": "DE",
                "rate": 19.0,
                "effective_date": "2025-01-01T00:00:00Z",
                "active_flag": False
            })
        # May succeed or return error if duplicate
        assert resp.status_code in (200, 201, 400, 409), f"super_admin tax-rate create unexpected: {resp.status_code}"
        print(f"✓ super_admin can create tax rate (status={resp.status_code})")


class TestContentPublishPermissions:
    """
    Content publish endpoints should only be accessible by:
    - super_admin: yes
    - country_admin: yes
    - admin/dealer/user: NO (403)
    """
    
    def test_super_admin_can_access_info_pages(self):
        """super_admin can access info pages"""
        resp = requests.get(f"{API}/admin/info-pages", headers=auth_header("super_admin"))
        assert resp.status_code == 200, f"super_admin info-pages failed: {resp.text}"
        print("✓ super_admin can access info pages")
    
    def test_country_admin_can_access_info_pages(self):
        """country_admin can access info pages"""
        resp = requests.get(f"{API}/admin/info-pages", headers=auth_header("country_admin"))
        assert resp.status_code == 200, f"country_admin info-pages failed: {resp.text}"
        print("✓ country_admin can access info pages")


class TestNegativeFinanceAccess:
    """
    Negative tests: unauthorized roles should get 403
    """
    
    def test_dealer_cannot_access_invoices(self):
        """dealer cannot access admin invoices → 403"""
        resp = requests.get(f"{API}/admin/invoices?country=DE", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer invoices access should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from admin/invoices (403)")
    
    def test_user_cannot_access_invoices(self):
        """user cannot access admin invoices → 403"""
        resp = requests.get(f"{API}/admin/invoices?country=DE", headers=auth_header("user"))
        assert resp.status_code == 403, f"user invoices access should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from admin/invoices (403)")
    
    def test_dealer_cannot_access_plans(self):
        """dealer cannot access admin plans → 403"""
        resp = requests.get(f"{API}/admin/plans", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer plans access should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from admin/plans (403)")
    
    def test_user_cannot_access_plans(self):
        """user cannot access admin plans → 403"""
        resp = requests.get(f"{API}/admin/plans", headers=auth_header("user"))
        assert resp.status_code == 403, f"user plans access should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from admin/plans (403)")
    
    def test_dealer_cannot_access_tax_rates(self):
        """dealer cannot access admin tax rates → 403"""
        resp = requests.get(f"{API}/admin/tax-rates", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer tax-rates access should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from admin/tax-rates (403)")
    
    def test_user_cannot_access_tax_rates(self):
        """user cannot access admin tax rates → 403"""
        resp = requests.get(f"{API}/admin/tax-rates", headers=auth_header("user"))
        assert resp.status_code == 403, f"user tax-rates access should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from admin/tax-rates (403)")
    
    def test_dealer_cannot_access_payments(self):
        """dealer cannot access admin payments → 403"""
        resp = requests.get(f"{API}/admin/payments", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer payments access should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from admin/payments (403)")
    
    def test_user_cannot_access_payments(self):
        """user cannot access admin payments → 403"""
        resp = requests.get(f"{API}/admin/payments", headers=auth_header("user"))
        assert resp.status_code == 403, f"user payments access should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from admin/payments (403)")


class TestNegativeExportAccess:
    """
    Negative tests: export should be blocked for non-authorized roles
    """
    
    def test_dealer_cannot_export_payments(self):
        """dealer cannot export payments → 403"""
        resp = requests.get(f"{API}/admin/payments/export/csv", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer payments export should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from payments export (403)")
    
    def test_user_cannot_export_payments(self):
        """user cannot export payments → 403"""
        resp = requests.get(f"{API}/admin/payments/export/csv", headers=auth_header("user"))
        assert resp.status_code == 403, f"user payments export should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from payments export (403)")
    
    def test_dealer_cannot_export_invoices(self):
        """dealer cannot export invoices → 403"""
        resp = requests.get(f"{API}/admin/invoices/export/csv", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer invoices export should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from invoices export (403)")
    
    def test_user_cannot_export_invoices(self):
        """user cannot export invoices → 403"""
        resp = requests.get(f"{API}/admin/invoices/export/csv", headers=auth_header("user"))
        assert resp.status_code == 403, f"user invoices export should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from invoices export (403)")


class TestNegativePublishAccess:
    """
    Negative tests: publish should be blocked for non-authorized roles
    """
    
    def test_dealer_cannot_access_info_pages(self):
        """dealer cannot access info pages → 403"""
        resp = requests.get(f"{API}/admin/info-pages", headers=auth_header("dealer"))
        assert resp.status_code == 403, f"dealer info-pages access should be 403, got {resp.status_code}"
        print("✓ dealer correctly blocked from info-pages (403)")
    
    def test_user_cannot_access_info_pages(self):
        """user cannot access info pages → 403"""
        resp = requests.get(f"{API}/admin/info-pages", headers=auth_header("user"))
        assert resp.status_code == 403, f"user info-pages access should be 403, got {resp.status_code}"
        print("✓ user correctly blocked from info-pages (403)")


class TestZeroRoleBypass:
    """
    Test that unauthenticated requests are blocked (401)
    """
    
    def test_no_token_invoices(self):
        """No token → 401/403 for admin invoices"""
        resp = requests.get(f"{API}/admin/invoices")
        assert resp.status_code in (401, 403), f"No token should be 401/403, got {resp.status_code}"
        print("✓ No token correctly blocked from admin/invoices")
    
    def test_no_token_plans(self):
        """No token → 401/403 for admin plans"""
        resp = requests.get(f"{API}/admin/plans")
        assert resp.status_code in (401, 403), f"No token should be 401/403, got {resp.status_code}"
        print("✓ No token correctly blocked from admin/plans")
    
    def test_no_token_export(self):
        """No token → 401/403 for export"""
        resp = requests.get(f"{API}/admin/payments/export/csv")
        assert resp.status_code in (401, 403), f"No token should be 401/403, got {resp.status_code}"
        print("✓ No token correctly blocked from export")
    
    def test_invalid_token(self):
        """Invalid token → 401 for admin endpoints"""
        resp = requests.get(f"{API}/admin/invoices", headers={"Authorization": "Bearer invalid-token-xyz"})
        assert resp.status_code in (401, 403), f"Invalid token should be 401, got {resp.status_code}"
        print("✓ Invalid token correctly blocked")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
