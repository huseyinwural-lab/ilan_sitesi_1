"""
Test suite for nightly_e2e_extended_runner.py - Task 3 (GÖREV 3)
Tests User/Dealer/Admin real flows for nightly capture.

Validation scope:
- User finance: PDF download + subscription cancel/reactivate
- Dealer flow: DE+FR listing submit/publish track
- Admin flow: finance export + webhook replay smoke
- CI merge gate logic: finance_e2e_pass/listing_e2e_pass false → merge_blocked true
- Artifact content: broken_flows + endpoint_http_4xx_5xx fields present
"""

import os
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip(f"Admin login failed: {resp.status_code}")


@pytest.fixture(scope="module")
def user_token():
    """Get user auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": USER_EMAIL, "password": USER_PASSWORD})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip(f"User login failed: {resp.status_code}")


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer auth token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD})
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip(f"Dealer login failed: {resp.status_code}")


class TestAuthentication:
    """Auth flow tests for all three roles"""

    def test_admin_login(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert resp.status_code == 200, f"Admin login failed: {resp.status_code}"
        data = resp.json()
        assert "access_token" in data, "No access_token in admin login response"

    def test_user_login(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": USER_EMAIL, "password": USER_PASSWORD})
        assert resp.status_code == 200, f"User login failed: {resp.status_code}"
        data = resp.json()
        assert "access_token" in data, "No access_token in user login response"

    def test_dealer_login(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD})
        assert resp.status_code == 200, f"Dealer login failed: {resp.status_code}"
        data = resp.json()
        assert "access_token" in data, "No access_token in dealer login response"


class TestUserFinanceFlow:
    """User finance PDF + subscription cancel/reactivate tests"""

    def test_account_invoices_list(self, user_token):
        """User can list their invoices"""
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = requests.get(f"{BASE_URL}/api/account/invoices", headers=headers)
        assert resp.status_code == 200, f"Account invoices list failed: {resp.status_code}"

    def test_subscription_cancel(self, user_token):
        """User can cancel subscription"""
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = requests.post(f"{BASE_URL}/api/account/subscription/cancel", headers=headers)
        assert resp.status_code == 200, f"Subscription cancel failed: {resp.status_code}"

    def test_subscription_reactivate(self, user_token):
        """User can reactivate subscription"""
        headers = {"Authorization": f"Bearer {user_token}"}
        resp = requests.post(f"{BASE_URL}/api/account/subscription/reactivate", headers=headers)
        assert resp.status_code == 200, f"Subscription reactivate failed: {resp.status_code}"

    def test_invoice_pdf_download_flow(self, user_token, admin_token):
        """Test full invoice PDF download flow"""
        user_headers = {"Authorization": f"Bearer {user_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Get invoice list
        resp = requests.get(f"{BASE_URL}/api/account/invoices", headers=user_headers)
        assert resp.status_code == 200

        items = (resp.json() or {}).get("items") or []
        if not items:
            # Create invoice if none exists
            user_me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=user_headers)
            assert user_me_resp.status_code == 200
            user_id = user_me_resp.json().get("id")

            plans_resp = requests.get(f"{BASE_URL}/api/admin/plans", headers=admin_headers)
            if plans_resp.status_code == 200:
                plans = (plans_resp.json() or {}).get("items") or []
                plan_id = plans[0].get("id") if plans else None
                payload = {"user_id": user_id, "issue_now": True}
                if plan_id:
                    payload["plan_id"] = plan_id
                create_resp = requests.post(f"{BASE_URL}/api/admin/invoices", headers=admin_headers, json=payload)
                if create_resp.status_code == 200:
                    invoice_id = ((create_resp.json() or {}).get("invoice") or {}).get("id")
                    if invoice_id:
                        # Generate PDF
                        requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/generate-pdf", headers=admin_headers)
                        # Download PDF
                        download_resp = requests.get(f"{BASE_URL}/api/account/invoices/{invoice_id}/download-pdf", headers=user_headers)
                        assert download_resp.status_code == 200, f"PDF download failed: {download_resp.status_code}"
                        return

        if items:
            invoice_id = items[0].get("id")
            # Generate PDF
            requests.post(f"{BASE_URL}/api/admin/invoices/{invoice_id}/generate-pdf", headers=admin_headers)
            # Download PDF
            download_resp = requests.get(f"{BASE_URL}/api/account/invoices/{invoice_id}/download-pdf", headers=user_headers)
            assert download_resp.status_code == 200, f"PDF download failed: {download_resp.status_code}"


class TestDealerListingFlow:
    """Dealer listing DE+FR submit/publish track tests"""

    def test_get_vehicle_category_de(self, dealer_token):
        """Get vehicle category for DE"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        resp = requests.get(f"{BASE_URL}/api/categories/children?module=vehicle&country=DE", headers=headers)
        assert resp.status_code == 200, f"Get category DE failed: {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list) and len(data) > 0, "No categories returned for DE"

    def test_get_vehicle_category_fr(self, dealer_token):
        """Get vehicle category for FR"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        resp = requests.get(f"{BASE_URL}/api/categories/children?module=vehicle&country=FR", headers=headers)
        assert resp.status_code == 200, f"Get category FR failed: {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list) and len(data) > 0, "No categories returned for FR"

    def test_de_listing_submit_track(self, dealer_token):
        """Full DE listing submit track: create→patch→preview→submit"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        # Get category
        cat_resp = requests.get(f"{BASE_URL}/api/categories/children?module=vehicle&country=DE", headers=headers)
        assert cat_resp.status_code == 200
        category_id = cat_resp.json()[0].get("id")

        # Create listing
        create_payload = {"category_id": category_id, "country": "DE", "title": "TEST_Nightly DE Submit Listing"}
        create_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle", headers=headers, json=create_payload)
        assert create_resp.status_code == 200, f"Create listing failed: {create_resp.status_code}"
        listing_id = create_resp.json().get("id")
        assert listing_id, "No listing ID returned"

        # Patch draft
        patch_payload = {
            "core_fields": {
                "title": "TEST_Nightly DE Submit Listing Updated",
                "description": "Test description",
                "price": {"price_type": "FIXED", "amount": 20000, "currency_primary": "EUR"}
            },
            "location": {"city": "Berlin", "country": "DE"}
        }
        patch_resp = requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=patch_payload)
        assert patch_resp.status_code == 200, f"Patch draft failed: {patch_resp.status_code}"

        # Preview ready
        preview_payload = {**patch_payload, "contact": {"contact_name": "Test Dealer", "contact_phone": "+491234567890"}}
        preview_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=preview_payload)
        assert preview_resp.status_code == 200, f"Preview ready failed: {preview_resp.status_code}"

        # Submit review
        import uuid
        submit_headers = {**headers, "Idempotency-Key": str(uuid.uuid4())}
        submit_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review", headers=submit_headers)
        assert submit_resp.status_code == 200, f"Submit review failed: {submit_resp.status_code}"

    def test_de_listing_publish_track(self, dealer_token):
        """Full DE listing publish track: create→patch→preview→publish"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        # Get category
        cat_resp = requests.get(f"{BASE_URL}/api/categories/children?module=vehicle&country=DE", headers=headers)
        assert cat_resp.status_code == 200
        category_id = cat_resp.json()[0].get("id")

        # Create listing
        create_payload = {"category_id": category_id, "country": "DE", "title": "TEST_Nightly DE Publish Listing"}
        create_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle", headers=headers, json=create_payload)
        assert create_resp.status_code == 200
        listing_id = create_resp.json().get("id")

        # Patch draft
        patch_payload = {
            "core_fields": {
                "title": "TEST_Nightly DE Publish Listing Updated",
                "description": "Test publish description",
                "price": {"price_type": "FIXED", "amount": 25000, "currency_primary": "EUR"}
            },
            "location": {"city": "Berlin", "country": "DE"}
        }
        patch_resp = requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=patch_payload)
        assert patch_resp.status_code == 200

        # Preview ready
        preview_payload = {**patch_payload, "contact": {"contact_name": "Test Dealer", "contact_phone": "+491234567890"}}
        preview_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=preview_payload)
        assert preview_resp.status_code == 200

        # Publish
        publish_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/publish", headers=headers)
        assert publish_resp.status_code == 200, f"Publish failed: {publish_resp.status_code}"

    def test_fr_listing_submit_track(self, dealer_token):
        """Full FR listing submit track"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        cat_resp = requests.get(f"{BASE_URL}/api/categories/children?module=vehicle&country=FR", headers=headers)
        assert cat_resp.status_code == 200
        category_id = cat_resp.json()[0].get("id")

        create_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle", headers=headers, 
            json={"category_id": category_id, "country": "FR", "title": "TEST_Nightly FR Submit Listing"})
        assert create_resp.status_code == 200
        listing_id = create_resp.json().get("id")

        patch_payload = {
            "core_fields": {
                "title": "TEST_Nightly FR Submit Listing Updated",
                "description": "Test FR description",
                "price": {"price_type": "FIXED", "amount": 18000, "currency_primary": "EUR"}
            },
            "location": {"city": "Paris", "country": "FR"}
        }
        patch_resp = requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=patch_payload)
        assert patch_resp.status_code == 200

        preview_payload = {**patch_payload, "contact": {"contact_name": "Test Dealer FR", "contact_phone": "+33123456789"}}
        preview_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=preview_payload)
        assert preview_resp.status_code == 200

        import uuid
        submit_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review", 
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())})
        assert submit_resp.status_code == 200

    def test_fr_listing_publish_track(self, dealer_token):
        """Full FR listing publish track"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        cat_resp = requests.get(f"{BASE_URL}/api/categories/children?module=vehicle&country=FR", headers=headers)
        assert cat_resp.status_code == 200
        category_id = cat_resp.json()[0].get("id")

        create_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle", headers=headers, 
            json={"category_id": category_id, "country": "FR", "title": "TEST_Nightly FR Publish Listing"})
        assert create_resp.status_code == 200
        listing_id = create_resp.json().get("id")

        patch_payload = {
            "core_fields": {
                "title": "TEST_Nightly FR Publish Listing Updated",
                "description": "Test FR publish description",
                "price": {"price_type": "FIXED", "amount": 22000, "currency_primary": "EUR"}
            },
            "location": {"city": "Paris", "country": "FR"}
        }
        patch_resp = requests.patch(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft", headers=headers, json=patch_payload)
        assert patch_resp.status_code == 200

        preview_payload = {**patch_payload, "contact": {"contact_name": "Test Dealer FR", "contact_phone": "+33123456789"}}
        preview_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready", headers=headers, json=preview_payload)
        assert preview_resp.status_code == 200

        publish_resp = requests.post(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/publish", headers=headers)
        assert publish_resp.status_code == 200


class TestAdminFlow:
    """Admin finance export + webhook replay smoke tests"""

    def test_finance_export_csv(self, admin_token):
        """Admin finance export CSV"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        resp = requests.get(f"{BASE_URL}/api/admin/payments/export/csv", headers=headers, timeout=60)
        assert resp.status_code == 200, f"Finance export CSV failed: {resp.status_code}"

    def test_webhook_replay_smoke(self, admin_token):
        """Webhook replay smoke test - expects 400 or 404 for fake event ID"""
        import uuid
        headers = {"Authorization": f"Bearer {admin_token}"}
        fake_event_id = str(uuid.uuid4())
        resp = requests.post(f"{BASE_URL}/api/admin/webhooks/events/{fake_event_id}/replay", headers=headers, json={})
        assert resp.status_code in [400, 404], f"Webhook replay smoke returned unexpected status: {resp.status_code}"


class TestNightlyReportStructure:
    """Validate nightly report structure and artifact requirements"""

    def test_report_file_exists(self):
        """Report file should exist after runner execution"""
        report_path = "/app/test_reports/nightly_e2e_extended.json"
        assert os.path.exists(report_path), f"Report file not found: {report_path}"

    def test_report_has_required_fields(self):
        """Report should have all required fields"""
        report_path = "/app/test_reports/nightly_e2e_extended.json"
        with open(report_path) as f:
            report = json.load(f)

        # Top-level required fields
        required_fields = ["generated_at", "mode", "runs", "base_url", "latest", "recent_runs", 
                          "last_five_nightly_pass", "ci_gate", "artifact_requirements"]
        for field in required_fields:
            assert field in report, f"Missing top-level field: {field}"

    def test_latest_run_structure(self):
        """Latest run should have proper structure"""
        with open("/app/test_reports/nightly_e2e_extended.json") as f:
            report = json.load(f)
        
        latest = report.get("latest", {})
        required = ["status", "flows", "broken_flows", "endpoint_http_4xx_5xx", "endpoint_events",
                   "finance_e2e_pass", "listing_e2e_pass", "merge_blocked"]
        for field in required:
            assert field in latest, f"Missing field in latest run: {field}"

    def test_flows_structure(self):
        """Flows should have user, dealer, admin"""
        with open("/app/test_reports/nightly_e2e_extended.json") as f:
            report = json.load(f)
        
        flows = report.get("latest", {}).get("flows", {})
        assert "user" in flows, "Missing user flow"
        assert "dealer" in flows, "Missing dealer flow"
        assert "admin" in flows, "Missing admin flow"

        # User flow structure
        user_flow = flows.get("user", {})
        assert "pdf_download_pass" in user_flow, "Missing pdf_download_pass in user flow"
        assert "subscription_cancel_reactivate_pass" in user_flow, "Missing subscription fields"

        # Dealer flow structure
        dealer_flow = flows.get("dealer", {})
        assert "de" in dealer_flow, "Missing DE in dealer flow"
        assert "fr" in dealer_flow, "Missing FR in dealer flow"
        for country in ["de", "fr"]:
            country_flow = dealer_flow.get(country, {})
            assert "submit_track" in country_flow, f"Missing submit_track in {country}"
            assert "publish_track" in country_flow, f"Missing publish_track in {country}"

        # Admin flow structure
        admin_flow = flows.get("admin", {})
        assert "finance_export_pass" in admin_flow, "Missing finance_export_pass"
        assert "webhook_replay_smoke_pass" in admin_flow, "Missing webhook_replay_smoke_pass"

    def test_ci_gate_structure(self):
        """CI gate should have merge_blocked, finance_gate, listing_gate"""
        with open("/app/test_reports/nightly_e2e_extended.json") as f:
            report = json.load(f)
        
        ci_gate = report.get("ci_gate", {})
        assert "merge_blocked" in ci_gate, "Missing merge_blocked in ci_gate"
        assert "finance_gate" in ci_gate, "Missing finance_gate in ci_gate"
        assert "listing_gate" in ci_gate, "Missing listing_gate in ci_gate"

    def test_artifact_requirements_structure(self):
        """Artifact requirements should have broken_flows and endpoint_http_4xx_5xx"""
        with open("/app/test_reports/nightly_e2e_extended.json") as f:
            report = json.load(f)
        
        artifact = report.get("artifact_requirements", {})
        assert "broken_flows" in artifact, "Missing broken_flows in artifact_requirements"
        assert "endpoint_http_4xx_5xx" in artifact, "Missing endpoint_http_4xx_5xx in artifact_requirements"


class TestMergeGateLogic:
    """Test CI merge gate logic: finance_e2e_pass/listing_e2e_pass false → merge_blocked true"""

    def test_merge_blocked_when_all_pass(self):
        """When all pass, merge_blocked should be false"""
        with open("/app/test_reports/nightly_e2e_extended.json") as f:
            report = json.load(f)
        
        latest = report.get("latest", {})
        if latest.get("finance_e2e_pass") and latest.get("listing_e2e_pass"):
            assert latest.get("merge_blocked") is False, "merge_blocked should be false when all pass"

    def test_ci_gate_reflects_latest(self):
        """CI gate should reflect latest run results"""
        with open("/app/test_reports/nightly_e2e_extended.json") as f:
            report = json.load(f)
        
        latest = report.get("latest", {})
        ci_gate = report.get("ci_gate", {})
        
        # merge_blocked in ci_gate should match latest
        assert ci_gate.get("merge_blocked") == latest.get("merge_blocked"), "CI gate merge_blocked mismatch"
        
        # finance_gate should be inverse of finance_e2e_pass
        assert ci_gate.get("finance_gate") == (not latest.get("finance_e2e_pass")), "Finance gate mismatch"
        
        # listing_gate should be inverse of listing_e2e_pass
        assert ci_gate.get("listing_gate") == (not latest.get("listing_e2e_pass")), "Listing gate mismatch"
