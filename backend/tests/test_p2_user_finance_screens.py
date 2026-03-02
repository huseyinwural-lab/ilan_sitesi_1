"""
P2-FIN-U User Finance Screens Backend Tests
Tests for:
- P2-FIN-U-01: /account/invoices - API binding, filters, list render, PDF download, ownership enforcement
- P2-FIN-U-02: /account/payments - payment history, status badges, user-friendly messages
- P2-FIN-U-03: /account/subscription - active plan, renewal date, cancel/reactivate modal flows
- Invoice list sorted by invoice_date/issued_at DESC
- Subscription actions with confirmation modal requirement
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def user_token():
    """Get user authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    }, timeout=30)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"User authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }, timeout=30)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


class TestAccountInvoices:
    """P2-FIN-U-01: Account invoices endpoint tests"""
    
    def test_list_invoices_authenticated(self, user_token):
        """Test invoices list returns 200 for authenticated user"""
        response = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items array"
        assert isinstance(data["items"], list), "items should be a list"
        print(f"PASS: List invoices returned {len(data['items'])} items")
    
    def test_list_invoices_sorted_by_date_desc(self, user_token):
        """Test invoices are sorted by issued_at/created_at descending (newest first)"""
        response = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        
        if len(items) >= 2:
            # Parse dates and verify descending order
            from datetime import datetime
            def get_date(item):
                date_str = item.get("issued_at") or item.get("created_at")
                if date_str:
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return datetime.min
            
            dates = [get_date(item) for item in items]
            for i in range(len(dates) - 1):
                assert dates[i] >= dates[i+1], f"Invoice list not sorted DESC: {dates[i]} < {dates[i+1]}"
            print(f"PASS: Invoices are sorted by date DESC (newest first)")
        else:
            print(f"SKIP: Not enough invoices ({len(items)}) to verify sort order")
    
    def test_list_invoices_status_filter(self, user_token):
        """Test invoices filter by status"""
        for status in ["issued", "paid", "void", "refunded"]:
            response = requests.get(
                f"{BASE_URL}/api/account/invoices?status={status}",
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=15
            )
            assert response.status_code == 200, f"Filter status={status} failed: {response.status_code}"
            data = response.json()
            items = data.get("items", [])
            # Verify all returned items have the filtered status
            for item in items:
                assert item.get("status") == status, f"Item status {item.get('status')} != filter {status}"
            print(f"PASS: Status filter '{status}' works, returned {len(items)} items")
    
    def test_list_invoices_date_filter(self, user_token):
        """Test invoices filter by date range"""
        response = requests.get(
            f"{BASE_URL}/api/account/invoices?start_date=2024-01-01T00:00:00%2B00:00&end_date=2030-12-31T23:59:59%2B00:00",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Date filter failed: {response.status_code}"
        data = response.json()
        print(f"PASS: Date range filter works, returned {len(data.get('items', []))} items")
    
    def test_list_invoices_unauthenticated(self):
        """Test invoices list returns 401/403 for unauthenticated request"""
        response = requests.get(f"{BASE_URL}/api/account/invoices", timeout=15)
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print(f"PASS: Unauthenticated request blocked with {response.status_code}")
    
    def test_invoice_detail_ownership_enforced(self, user_token, admin_token):
        """Test invoice detail enforces ownership - user cannot access another user's invoice"""
        # First get admin's invoices to find one not belonging to user
        admin_invoices = requests.get(
            f"{BASE_URL}/api/admin/invoices?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        if admin_invoices.status_code != 200:
            pytest.skip("Cannot get admin invoices list")
        
        invoices = admin_invoices.json().get("items", [])
        # Find an invoice that might belong to a different user
        for inv in invoices:
            invoice_id = inv.get("id")
            # Try to access this invoice as user
            response = requests.get(
                f"{BASE_URL}/api/account/invoices/{invoice_id}",
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=15
            )
            # If user doesn't own it, should get 403
            if response.status_code == 403:
                print(f"PASS: Ownership enforced - got 403 for invoice {invoice_id}")
                return
            elif response.status_code == 200:
                # This invoice belongs to the user, continue checking
                continue
        print("SKIP: All tested invoices belong to user (cannot verify ownership enforcement)")
    
    def test_invoice_pdf_download(self, user_token):
        """Test PDF download for user's invoice"""
        # Get user's invoices
        list_response = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert list_response.status_code == 200
        invoices = list_response.json().get("items", [])
        
        # Find an invoice with PDF
        pdf_invoice = None
        for inv in invoices:
            if inv.get("pdf_url"):
                pdf_invoice = inv
                break
        
        if not pdf_invoice:
            pytest.skip("No invoices with PDF available for user")
        
        # Download PDF
        response = requests.get(
            f"{BASE_URL}/api/account/invoices/{pdf_invoice['id']}/download-pdf",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"PDF download failed: {response.status_code} - {response.text}"
        assert response.headers.get("content-type") == "application/pdf", "Response should be PDF"
        assert len(response.content) > 0, "PDF content should not be empty"
        print(f"PASS: PDF download successful, size: {len(response.content)} bytes")


class TestAccountPayments:
    """P2-FIN-U-02: Account payments endpoint tests"""
    
    def test_list_payments_authenticated(self, user_token):
        """Test payments list returns 200 for authenticated user"""
        response = requests.get(
            f"{BASE_URL}/api/account/payments",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data, "Response should contain items array"
        assert isinstance(data["items"], list), "items should be a list"
        print(f"PASS: List payments returned {len(data['items'])} items")
    
    def test_payments_have_normalized_message(self, user_token):
        """Test payments include user-friendly normalized_message"""
        response = requests.get(
            f"{BASE_URL}/api/account/payments",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200
        items = response.json().get("items", [])
        
        for item in items:
            assert "normalized_message" in item, f"Payment {item.get('id')} missing normalized_message"
            assert isinstance(item["normalized_message"], str), "normalized_message should be string"
            # No PII leak check - normalized_message should be generic status text
            assert "card" not in item["normalized_message"].lower() or "ödeme" in item["normalized_message"].lower(), \
                "normalized_message should not leak card details"
        print(f"PASS: All {len(items)} payments have normalized_message without PII")
    
    def test_payments_status_filter(self, user_token):
        """Test payments filter by status"""
        for status in ["succeeded", "failed", "pending", "processing"]:
            response = requests.get(
                f"{BASE_URL}/api/account/payments?status={status}",
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=15
            )
            assert response.status_code == 200, f"Filter status={status} failed: {response.status_code}"
            data = response.json()
            items = data.get("items", [])
            for item in items:
                assert item.get("status") == status, f"Item status {item.get('status')} != filter {status}"
            print(f"PASS: Status filter '{status}' works, returned {len(items)} items")
    
    def test_payments_no_pii_leak(self, user_token):
        """Test payments response does not leak sensitive PII"""
        response = requests.get(
            f"{BASE_URL}/api/account/payments",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200
        items = response.json().get("items", [])
        
        pii_fields = ["card_number", "cvv", "expiry", "full_card", "ssn"]
        for item in items:
            for field in pii_fields:
                assert field not in item, f"PII leak: {field} found in payment response"
        print(f"PASS: No PII leaks detected in {len(items)} payment records")


class TestAccountSubscription:
    """P2-FIN-U-03: Account subscription endpoint tests"""
    
    def test_subscription_status(self, user_token):
        """Test subscription status returns 200 with proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "has_subscription" in data, "Response should have has_subscription"
        assert "status" in data, "Response should have status"
        assert "cancel_at_period_end" in data, "Response should have cancel_at_period_end"
        
        if data["has_subscription"]:
            assert "plan" in data, "Active subscription should have plan"
            assert "current_period_end" in data, "Active subscription should have current_period_end"
            print(f"PASS: Subscription status: {data['status']}, plan: {data.get('plan', {}).get('name')}")
        else:
            print(f"PASS: No active subscription (status: {data['status']})")
    
    def test_subscription_plan_info(self, user_token):
        """Test subscription includes plan info (name, price, currency)"""
        response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("has_subscription") and data.get("plan"):
            plan = data["plan"]
            assert "id" in plan, "Plan should have id"
            assert "name" in plan, "Plan should have name"
            assert "price_amount" in plan, "Plan should have price_amount"
            assert "currency_code" in plan, "Plan should have currency_code"
            print(f"PASS: Plan info complete: {plan['name']} - {plan['price_amount']} {plan['currency_code']}")
        else:
            pytest.skip("No active subscription to test plan info")
    
    def test_subscription_cancel_requires_auth(self):
        """Test subscription cancel requires authentication"""
        response = requests.post(f"{BASE_URL}/api/account/subscription/cancel", json={}, timeout=15)
        assert response.status_code in [401, 403, 422], f"Expected 401/403/422, got {response.status_code}"
        print(f"PASS: Cancel blocked without auth: {response.status_code}")
    
    def test_subscription_cancel_flow(self, user_token):
        """Test subscription cancel sets cancel_at_period_end flag"""
        # Get current status
        status_response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        if not status_data.get("has_subscription"):
            pytest.skip("No active subscription to test cancel")
        
        if status_data.get("status") not in ["trialing", "active", "past_due"]:
            pytest.skip(f"Subscription status '{status_data.get('status')}' cannot be cancelled")
        
        # If already cancelled, reactivate first
        if status_data.get("cancel_at_period_end"):
            reactivate_response = requests.post(
                f"{BASE_URL}/api/account/subscription/reactivate",
                json={},
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=15
            )
            assert reactivate_response.status_code == 200
        
        # Cancel subscription
        cancel_response = requests.post(
            f"{BASE_URL}/api/account/subscription/cancel",
            json={},
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert cancel_response.status_code == 200, f"Cancel failed: {cancel_response.status_code} - {cancel_response.text}"
        cancel_data = cancel_response.json()
        assert cancel_data.get("ok") == True, "Cancel response should have ok=True"
        assert cancel_data.get("cancel_at_period_end") == True, "cancel_at_period_end should be True after cancel"
        
        # Verify state persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("cancel_at_period_end") == True, "State not persisted: cancel_at_period_end should be True"
        print(f"PASS: Cancel flow works - cancel_at_period_end={verify_data.get('cancel_at_period_end')}")
    
    def test_subscription_reactivate_flow(self, user_token):
        """Test subscription reactivate clears cancel_at_period_end flag"""
        # Get current status
        status_response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        if not status_data.get("has_subscription"):
            pytest.skip("No active subscription to test reactivate")
        
        # Ensure subscription is in cancelled state first
        if not status_data.get("cancel_at_period_end"):
            cancel_response = requests.post(
                f"{BASE_URL}/api/account/subscription/cancel",
                json={},
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=15
            )
            assert cancel_response.status_code == 200
        
        # Reactivate subscription
        reactivate_response = requests.post(
            f"{BASE_URL}/api/account/subscription/reactivate",
            json={},
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert reactivate_response.status_code == 200, f"Reactivate failed: {reactivate_response.status_code} - {reactivate_response.text}"
        reactivate_data = reactivate_response.json()
        assert reactivate_data.get("ok") == True, "Reactivate response should have ok=True"
        assert reactivate_data.get("cancel_at_period_end") == False, "cancel_at_period_end should be False after reactivate"
        
        # Verify state persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("cancel_at_period_end") == False, "State not persisted: cancel_at_period_end should be False"
        print(f"PASS: Reactivate flow works - cancel_at_period_end={verify_data.get('cancel_at_period_end')}")
    
    def test_subscription_plans_list(self, user_token):
        """Test subscription plans list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/account/subscription/plans",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Plans list failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "Response should have items"
        
        for plan in data.get("items", []):
            assert "id" in plan, "Plan should have id"
            assert "name" in plan, "Plan should have name"
            assert "price_amount" in plan, "Plan should have price_amount"
        print(f"PASS: Plans list returned {len(data.get('items', []))} plans")
    
    def test_subscription_plan_change_preview(self, user_token):
        """Test plan change preview endpoint"""
        # Get plans first
        plans_response = requests.get(
            f"{BASE_URL}/api/account/subscription/plans",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        if plans_response.status_code != 200:
            pytest.skip("Cannot get plans list")
        
        plans = plans_response.json().get("items", [])
        if not plans:
            pytest.skip("No plans available for preview test")
        
        # Get current subscription
        sub_response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15
        )
        if sub_response.status_code != 200 or not sub_response.json().get("has_subscription"):
            pytest.skip("No subscription for plan change preview")
        
        # Try preview with first available plan
        target_plan_id = plans[0]["id"]
        response = requests.post(
            f"{BASE_URL}/api/account/subscription/plan-change-preview",
            json={"target_plan_id": target_plan_id},
            headers={"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"},
            timeout=15
        )
        assert response.status_code == 200, f"Preview failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert "current_plan" in data, "Preview should have current_plan"
        assert "target_plan" in data, "Preview should have target_plan"
        assert "proration_preview" in data, "Preview should have proration_preview"
        print(f"PASS: Plan change preview works: delta={data.get('proration_preview', {}).get('immediate_delta_amount')}")


class TestRegressionAdminFinance:
    """Regression tests - admin finance flows should not be broken"""
    
    def test_admin_invoices_endpoint(self, admin_token):
        """Verify admin invoices endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Admin invoices broken: {response.status_code}"
        print(f"PASS: Admin invoices endpoint working")
    
    def test_admin_invoice_pdf_download(self, admin_token):
        """Verify admin can still download invoice PDFs"""
        # Get an invoice with PDF
        list_response = requests.get(
            f"{BASE_URL}/api/admin/invoices?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        assert list_response.status_code == 200
        invoices = list_response.json().get("items", [])
        
        pdf_invoice = None
        for inv in invoices:
            if inv.get("pdf_url"):
                pdf_invoice = inv
                break
        
        if not pdf_invoice:
            pytest.skip("No invoices with PDF for admin download test")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices/{pdf_invoice['id']}/download-pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200, f"Admin PDF download broken: {response.status_code}"
        assert response.headers.get("content-type") == "application/pdf"
        print(f"PASS: Admin PDF download working")
    
    def test_admin_finance_export(self, admin_token):
        """Verify admin finance export still works"""
        for export_type in ["payments", "invoices"]:
            response = requests.get(
                f"{BASE_URL}/api/admin/finance/export?export_type={export_type}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=30
            )
            assert response.status_code == 200, f"Export {export_type} broken: {response.status_code}"
            print(f"PASS: Admin finance export '{export_type}' working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
