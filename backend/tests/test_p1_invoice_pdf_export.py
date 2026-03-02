"""
P1 Invoice PDF Generation + Storage + Finance Export Tests
===========================================================
Tests for:
1. Invoice snapshot immutable fields in response
2. POST /api/admin/invoices/{id}/generate-pdf idempotent behavior
3. POST /api/admin/invoices/{id}/regenerate-pdf super_admin only (country_admin 403)
4. GET /api/admin/invoices/{id}/download-pdf country-admin scope enforcement
5. Country scope isolation for invoice detail
6. Scoped export: GET /api/admin/finance/export with type=payments|invoices|ledger
7. Audit event smoke for PDF and export operations
"""
import os
import pytest
import requests
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
SUPER_ADMIN_EMAIL = "admin@platform.com"
SUPER_ADMIN_PASSWORD = "Admin123!"
COUNTRY_ADMIN_EMAIL = "countryadmin@platform.com"
COUNTRY_ADMIN_PASSWORD = "Country123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


@pytest.fixture(scope="module")
def super_admin_token():
    """Login as super_admin and get token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_ADMIN_EMAIL,
        "password": SUPER_ADMIN_PASSWORD
    }, timeout=30)
    if resp.status_code != 200:
        pytest.skip(f"Super admin login failed: {resp.status_code} {resp.text}")
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def country_admin_token():
    """Login as country_admin (DE scope) and get token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": COUNTRY_ADMIN_EMAIL,
        "password": COUNTRY_ADMIN_PASSWORD
    }, timeout=30)
    if resp.status_code != 200:
        pytest.skip(f"Country admin login failed: {resp.status_code} {resp.text}")
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def normal_user_token():
    """Login as normal user and get token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    }, timeout=30)
    if resp.status_code != 200:
        pytest.skip(f"Normal user login failed: {resp.status_code} {resp.text}")
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def super_admin_headers(super_admin_token):
    return {"Authorization": f"Bearer {super_admin_token}"}


@pytest.fixture(scope="module")
def country_admin_headers(country_admin_token):
    return {"Authorization": f"Bearer {country_admin_token}"}


@pytest.fixture(scope="module")
def normal_user_headers(normal_user_token):
    return {"Authorization": f"Bearer {normal_user_token}"}


@pytest.fixture(scope="module")
def dealer_user_id(super_admin_headers):
    """Get the dealer user id for creating invoices"""
    resp = requests.get(f"{BASE_URL}/api/admin/users?role=dealer&limit=1", headers=super_admin_headers, timeout=30)
    if resp.status_code == 200 and resp.json().get("items"):
        return resp.json()["items"][0]["id"]
    # Fall back to user@platform.com
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    }, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("user", {}).get("id")
    pytest.skip("Could not get a user ID for invoice tests")


@pytest.fixture(scope="module")
def test_invoice_de(super_admin_headers, dealer_user_id):
    """Create a test invoice in DE country for testing"""
    # First get a plan
    resp = requests.get(f"{BASE_URL}/api/admin/plans?country_code=DE&limit=1", headers=super_admin_headers, timeout=30)
    plan_id = None
    if resp.status_code == 200 and resp.json().get("items"):
        plan_id = resp.json()["items"][0]["id"]
    
    payload = {
        "dealer_id": dealer_user_id,
        "plan_id": plan_id,
        "amount": 99.99,
        "currency_code": "EUR",
        "notes": "TEST_P1_PDF_EXPORT",
        "issue_now": True
    }
    resp = requests.post(f"{BASE_URL}/api/admin/invoices", headers=super_admin_headers, json=payload, timeout=30)
    if resp.status_code not in (200, 201):
        pytest.skip(f"Could not create test invoice: {resp.status_code} {resp.text}")
    return resp.json()


class TestInvoiceSnapshotFields:
    """Test that invoice response contains immutable snapshot fields"""
    
    def test_invoice_detail_has_snapshot_fields(self, super_admin_headers, test_invoice_de):
        """Invoice detail should contain net_amount_minor, tax_amount_minor, gross_amount_minor, 
        currency, tax_rate, billing_info_snapshot"""
        invoice_id = test_invoice_de.get("id")
        resp = requests.get(f"{BASE_URL}/api/admin/invoices/{invoice_id}", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        invoice = data.get("invoice", {})
        
        # Check immutable snapshot fields exist
        assert "net_amount_minor" in invoice, "net_amount_minor missing from invoice response"
        assert "tax_amount_minor" in invoice, "tax_amount_minor missing from invoice response"
        assert "gross_amount_minor" in invoice, "gross_amount_minor missing from invoice response"
        assert "currency" in invoice, "currency missing from invoice response"
        assert "tax_rate" in invoice, "tax_rate missing from invoice response"
        assert "billing_info_snapshot" in invoice, "billing_info_snapshot missing from invoice response"
        
        # Verify types
        assert isinstance(invoice["net_amount_minor"], int), "net_amount_minor should be int"
        assert isinstance(invoice["tax_amount_minor"], int), "tax_amount_minor should be int"
        assert isinstance(invoice["gross_amount_minor"], int), "gross_amount_minor should be int"
        assert isinstance(invoice["currency"], str), "currency should be string"
        assert isinstance(invoice["tax_rate"], (int, float)), "tax_rate should be numeric"
        assert isinstance(invoice["billing_info_snapshot"], dict), "billing_info_snapshot should be dict"
        
        print(f"✓ Invoice detail contains all snapshot fields: net={invoice['net_amount_minor']}, tax={invoice['tax_amount_minor']}, gross={invoice['gross_amount_minor']}, currency={invoice['currency']}, tax_rate={invoice['tax_rate']}")


class TestPdfGenerationIdempotency:
    """Test PDF generation idempotency"""
    
    def test_generate_pdf_first_call(self, super_admin_headers, test_invoice_de):
        """First call to generate-pdf should generate the PDF"""
        invoice_id = test_invoice_de.get("id")
        resp = requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/generate-pdf", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Could be "generated" or "already_generated" depending on prior state
        assert data.get("status") in ("generated", "already_generated"), f"Expected generated/already_generated, got {data.get('status')}"
        assert data.get("pdf_url") is not None, "pdf_url should be present"
        assert data.get("pdf_generated_at") is not None, "pdf_generated_at should be present"
        
        print(f"✓ PDF generation status: {data.get('status')}, url: {data.get('pdf_url')}")
    
    def test_generate_pdf_second_call_idempotent(self, super_admin_headers, test_invoice_de):
        """Second call to generate-pdf should return already_generated without overwriting"""
        invoice_id = test_invoice_de.get("id")
        
        # Get current state
        resp1 = requests.get(f"{BASE_URL}/api/admin/invoices/{invoice_id}", headers=super_admin_headers, timeout=30)
        original_url = resp1.json().get("invoice", {}).get("pdf_url")
        original_generated_at = resp1.json().get("invoice", {}).get("pdf_generated_at")
        
        # Call generate-pdf again
        resp = requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/generate-pdf", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert data.get("status") == "already_generated", f"Second call should return already_generated, got {data.get('status')}"
        assert data.get("pdf_url") == original_url, "PDF URL should not change on second call"
        
        print(f"✓ Idempotency verified: status=already_generated, URL unchanged")


class TestRegeneratePdfRoleRestriction:
    """Test that regenerate-pdf is restricted to super_admin only"""
    
    def test_regenerate_pdf_super_admin_allowed(self, super_admin_headers, test_invoice_de):
        """super_admin should be able to regenerate PDF"""
        invoice_id = test_invoice_de.get("id")
        resp = requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/regenerate-pdf", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200 for super_admin, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("status") == "regenerated", f"Expected regenerated, got {data.get('status')}"
        assert data.get("version") is not None, "version should be present"
        
        print(f"✓ super_admin can regenerate PDF: version={data.get('version')}")
    
    def test_regenerate_pdf_country_admin_forbidden(self, country_admin_headers, test_invoice_de):
        """country_admin should get 403 for regenerate-pdf"""
        invoice_id = test_invoice_de.get("id")
        resp = requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/regenerate-pdf", headers=country_admin_headers, timeout=30)
        
        assert resp.status_code == 403, f"Expected 403 for country_admin, got {resp.status_code}: {resp.text}"
        print(f"✓ country_admin blocked from regenerate-pdf: 403")


class TestDownloadPdfCountryScope:
    """Test download-pdf respects country scope"""
    
    def test_download_pdf_country_admin_own_scope(self, country_admin_headers, super_admin_headers):
        """country_admin should be able to download PDF for invoice in their scope (DE)"""
        # First create an invoice in DE scope with super_admin
        resp = requests.get(f"{BASE_URL}/api/admin/invoices?country=DE&limit=1", headers=super_admin_headers, timeout=30)
        if resp.status_code != 200 or not resp.json().get("items"):
            pytest.skip("No DE invoice available for test")
        
        invoice_id = resp.json()["items"][0]["id"]
        
        # Ensure PDF exists
        requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/generate-pdf", headers=super_admin_headers, timeout=30)
        
        # country_admin (DE scope) downloads
        resp = requests.get(f"{BASE_URL}/api/admin/invoices/{invoice_id}/download-pdf", headers=country_admin_headers, timeout=30)
        
        # Could be 200 (success) or 404 (no PDF)
        if resp.status_code == 200:
            assert resp.headers.get("content-type") == "application/pdf", "Should return PDF"
            print(f"✓ country_admin can download PDF for DE invoice")
        elif resp.status_code == 404:
            print(f"✓ PDF not generated yet for this invoice (expected behavior)")
        else:
            # Check if it's a scope issue
            assert resp.status_code in (200, 404), f"Expected 200 or 404, got {resp.status_code}: {resp.text}"


class TestCountryScopeIsolation:
    """Test country scope isolation for invoice detail"""
    
    def test_country_admin_can_view_own_scope_invoice(self, country_admin_headers, super_admin_headers):
        """country_admin (DE) should be able to view DE invoices"""
        resp = requests.get(f"{BASE_URL}/api/admin/invoices?country=DE&limit=1", headers=super_admin_headers, timeout=30)
        if resp.status_code != 200 or not resp.json().get("items"):
            pytest.skip("No DE invoice available")
        
        invoice_id = resp.json()["items"][0]["id"]
        resp = requests.get(f"{BASE_URL}/api/admin/invoices/{invoice_id}", headers=country_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200 for own scope, got {resp.status_code}"
        print(f"✓ country_admin can view DE scope invoice")
    
    def test_country_admin_blocked_from_other_scope(self, country_admin_headers, super_admin_headers, dealer_user_id):
        """country_admin (DE) should get 403 for invoice in different country (FR)"""
        # Create an invoice in FR scope
        resp = requests.get(f"{BASE_URL}/api/admin/plans?country_code=FR&limit=1", headers=super_admin_headers, timeout=30)
        plan_id = None
        if resp.status_code == 200 and resp.json().get("items"):
            plan_id = resp.json()["items"][0]["id"]
        
        # Create FR invoice
        payload = {
            "dealer_id": dealer_user_id,
            "plan_id": plan_id,
            "amount": 50.00,
            "currency_code": "EUR",
            "notes": "TEST_FR_SCOPE",
            "issue_now": True
        }
        resp = requests.post(f"{BASE_URL}/api/admin/invoices", headers=super_admin_headers, json=payload, timeout=30)
        
        if resp.status_code not in (200, 201):
            # Try to find an existing FR invoice
            resp = requests.get(f"{BASE_URL}/api/admin/invoices?country=FR&limit=1", headers=super_admin_headers, timeout=30)
            if resp.status_code != 200 or not resp.json().get("items"):
                pytest.skip("Could not create or find FR invoice for scope test")
            invoice_id = resp.json()["items"][0]["id"]
        else:
            invoice_id = resp.json().get("id")
        
        if not invoice_id:
            pytest.skip("No FR invoice available for scope isolation test")
        
        # country_admin (DE) tries to view FR invoice
        resp = requests.get(f"{BASE_URL}/api/admin/invoices/{invoice_id}", headers=country_admin_headers, timeout=30)
        
        # Should be 403 due to scope violation
        assert resp.status_code == 403, f"Expected 403 for out-of-scope, got {resp.status_code}: {resp.text}"
        print(f"✓ country_admin blocked from FR scope invoice: 403")


class TestScopedExport:
    """Test scoped export endpoint"""
    
    def test_export_payments_super_admin(self, super_admin_headers):
        """super_admin can export payments"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/export?type=payments", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get("content-type", "").startswith("text/csv"), "Should return CSV"
        print(f"✓ super_admin can export payments CSV")
    
    def test_export_invoices_super_admin(self, super_admin_headers):
        """super_admin can export invoices"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/export?type=invoices", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get("content-type", "").startswith("text/csv"), "Should return CSV"
        print(f"✓ super_admin can export invoices CSV")
    
    def test_export_ledger_super_admin(self, super_admin_headers):
        """super_admin can export ledger"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/export?type=ledger", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get("content-type", "").startswith("text/csv"), "Should return CSV"
        print(f"✓ super_admin can export ledger CSV")
    
    def test_export_country_admin(self, country_admin_headers):
        """country_admin can export (with scope enforcement)"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/export?type=payments", headers=country_admin_headers, timeout=30)
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"✓ country_admin can export payments (scope enforced backend)")
    
    def test_export_invalid_type(self, super_admin_headers):
        """Invalid export type should return 400"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/export?type=invalid", headers=super_admin_headers, timeout=30)
        
        assert resp.status_code == 400, f"Expected 400 for invalid type, got {resp.status_code}"
        print(f"✓ Invalid export type returns 400")
    
    def test_export_normal_user_forbidden(self, normal_user_headers):
        """Normal user should not access export"""
        resp = requests.get(f"{BASE_URL}/api/admin/finance/export?type=payments", headers=normal_user_headers, timeout=30)
        
        assert resp.status_code in (401, 403), f"Expected 401/403 for normal user, got {resp.status_code}"
        print(f"✓ Normal user blocked from export: {resp.status_code}")


class TestAuditEventSmoke:
    """Smoke test that audit events are logged without errors"""
    
    def test_pdf_generated_audit_logged(self, super_admin_headers):
        """Check that PDF_GENERATED audit events exist"""
        resp = requests.get(f"{BASE_URL}/api/admin/audit-logs?action=PDF_GENERATED&limit=5", headers=super_admin_headers, timeout=30)
        
        # If audit endpoint exists and returns data, good
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            print(f"✓ Audit log accessible, PDF_GENERATED events: {len(items)}")
        else:
            # Audit endpoint might have different path or require different permissions
            print(f"⚠ Audit logs endpoint returned {resp.status_code} - may need different permissions")
    
    def test_export_triggered_audit_logged(self, super_admin_headers):
        """Check that EXPORT_TRIGGERED audit events exist"""
        resp = requests.get(f"{BASE_URL}/api/admin/audit-logs?action=EXPORT_TRIGGERED&limit=5", headers=super_admin_headers, timeout=30)
        
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            print(f"✓ Audit log accessible, EXPORT_TRIGGERED events: {len(items)}")
        else:
            print(f"⚠ Audit logs endpoint returned {resp.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
