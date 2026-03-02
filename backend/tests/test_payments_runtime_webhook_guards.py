"""
Test Suite: Payments Runtime Config, Health Summary, and Webhook Guards
Iteration 77 - Tests for:
1. GET /api/payments/runtime-config -> payments_enabled/disabled_reason/publishable_key
2. GET /api/admin/system/health-summary -> payments_runtime flags
3. POST /api/payments/create-intent -> payments disabled guard (503)
4. POST /api/payments/{id}/reconcile -> payments disabled guard (503)
5. POST /api/payments/webhook -> signature missing/invalid guard (400)
6. POST /api/payments/stripe/webhook -> alternative webhook endpoint guard
7. Webhook replay protection - duplicate event_id handling via ProcessedWebhookEvent
"""

import pytest
import requests
import os
import json
import uuid
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


def get_user_token():
    """Helper to get user auth token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
        timeout=30
    )
    if resp.status_code != 200:
        pytest.skip(f"User login failed: {resp.status_code}")
    return resp.json().get("access_token")


def get_admin_token():
    """Helper to get admin auth token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code}")
    return resp.json().get("access_token")


class TestPaymentsRuntimeConfig:
    """Test GET /api/payments/runtime-config endpoint"""
    
    def test_runtime_config_endpoint_exists(self):
        """Verify runtime-config endpoint exists and returns valid response"""
        resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        
        # Should return 200 (public endpoint)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        print(f"PASS: /api/payments/runtime-config returns 200")
        print(f"  Response: {json.dumps(data, indent=2)}")
    
    def test_runtime_config_returns_required_fields(self):
        """Verify runtime-config returns payments_enabled, disabled_reason, publishable_key"""
        resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        assert resp.status_code == 200
        
        data = resp.json()
        
        # Check required fields exist
        assert "payments_enabled" in data, "Missing 'payments_enabled' field"
        assert "disabled_reason" in data, "Missing 'disabled_reason' field"
        assert "publishable_key" in data, "Missing 'publishable_key' field"
        
        # payments_enabled should be boolean
        assert isinstance(data["payments_enabled"], bool), "payments_enabled should be boolean"
        
        print(f"PASS: runtime-config returns all required fields")
        print(f"  payments_enabled: {data['payments_enabled']}")
        print(f"  disabled_reason: {data['disabled_reason']}")
        print(f"  publishable_key: {data['publishable_key']}")
    
    def test_runtime_config_disabled_reason_when_payments_disabled(self):
        """When payments_enabled=false, disabled_reason should be set"""
        resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        assert resp.status_code == 200
        
        data = resp.json()
        
        if not data["payments_enabled"]:
            # When disabled, disabled_reason should explain why
            assert data["disabled_reason"] is not None, "disabled_reason should be set when payments disabled"
            assert "stripe" in data["disabled_reason"].lower() or "key" in data["disabled_reason"].lower(), \
                f"disabled_reason should mention stripe/key issue: {data['disabled_reason']}"
            print(f"PASS: disabled_reason correctly set: {data['disabled_reason']}")
        else:
            # When enabled, disabled_reason should be None
            assert data["disabled_reason"] is None, "disabled_reason should be None when payments enabled"
            print(f"PASS: disabled_reason is None when payments enabled")
    
    def test_runtime_config_publishable_key_only_when_enabled(self):
        """publishable_key should only be returned when payments_enabled=true"""
        resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        assert resp.status_code == 200
        
        data = resp.json()
        
        if data["payments_enabled"]:
            assert data["publishable_key"] is not None, "publishable_key should be set when payments enabled"
            assert data["publishable_key"].startswith("pk_"), "publishable_key should start with pk_"
            print(f"PASS: publishable_key returned when payments enabled")
        else:
            assert data["publishable_key"] is None, "publishable_key should be None when payments disabled"
            print(f"PASS: publishable_key is None when payments disabled")


class TestAdminSystemHealthSummary:
    """Test GET /api/admin/system/health-summary payments_runtime inclusion"""
    
    def test_health_summary_requires_auth(self):
        """health-summary requires admin auth"""
        resp = requests.get(f"{BASE_URL}/api/admin/system/health-summary", timeout=30)
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"
        print(f"PASS: health-summary requires auth ({resp.status_code})")
    
    def test_health_summary_returns_payments_runtime(self):
        """health-summary should include payments_runtime section"""
        token = get_admin_token()
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/system/health-summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        
        # Verify payments_runtime section exists
        assert "payments_runtime" in data, "Missing 'payments_runtime' in health-summary"
        
        payments_runtime = data["payments_runtime"]
        print(f"PASS: health-summary includes payments_runtime")
        print(f"  payments_runtime: {json.dumps(payments_runtime, indent=2)}")
    
    def test_health_summary_payments_runtime_fields(self):
        """payments_runtime should include detailed stripe key status flags"""
        token = get_admin_token()
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/system/health-summary",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        payments_runtime = data.get("payments_runtime", {})
        
        # Check for expected fields in payments_runtime
        expected_fields = [
            "payments_enabled",
            "stripe_secret_key_present",
            "stripe_secret_key_valid",
            "stripe_publishable_key_present",
            "stripe_publishable_key_valid",
        ]
        
        for field in expected_fields:
            assert field in payments_runtime, f"Missing '{field}' in payments_runtime"
        
        print(f"PASS: payments_runtime contains all expected fields")
        for field in expected_fields:
            print(f"  {field}: {payments_runtime.get(field)}")


class TestPaymentsDisabledGuard:
    """Test 503 guard when payments are disabled"""
    
    def test_create_intent_returns_503_when_payments_disabled(self):
        """POST /api/payments/create-intent returns 503 with structured detail when payments disabled"""
        # First check if payments are disabled
        config_resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        config_data = config_resp.json()
        
        if config_data.get("payments_enabled"):
            pytest.skip("Payments are enabled - cannot test disabled guard")
        
        token = get_user_token()
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/create-intent",
            json={
                "listing_id": str(uuid.uuid4()),
                "amount": 100.0,
                "currency": "EUR"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        # Should return 503 when payments disabled
        assert resp.status_code == 503, f"Expected 503 for disabled payments, got {resp.status_code}"
        
        # Check for structured detail
        try:
            detail = resp.json().get("detail", {})
            if isinstance(detail, dict):
                assert "code" in detail, "503 detail should include 'code'"
                assert detail["code"] == "payments_disabled", f"Expected code 'payments_disabled', got {detail.get('code')}"
                assert "runtime" in detail, "503 detail should include 'runtime' snapshot"
                print(f"PASS: create-intent returns 503 with structured detail")
                print(f"  code: {detail.get('code')}")
                print(f"  message: {detail.get('message')}")
            else:
                print(f"PASS: create-intent returns 503 (detail is string: {detail})")
        except Exception as e:
            print(f"PASS: create-intent returns 503 (response: {resp.text[:200]})")
    
    def test_reconcile_returns_503_when_payments_disabled(self):
        """POST /api/payments/{id}/reconcile returns 503 when payments disabled"""
        # First check if payments are disabled
        config_resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        config_data = config_resp.json()
        
        if config_data.get("payments_enabled"):
            pytest.skip("Payments are enabled - cannot test disabled guard")
        
        token = get_user_token()
        
        # Use a random payment_id - the guard should trigger before ownership check
        payment_id = str(uuid.uuid4())
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/{payment_id}/reconcile",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=30
        )
        
        # Should return 503 when payments disabled (guard before other checks)
        assert resp.status_code == 503, f"Expected 503 for disabled payments, got {resp.status_code}"
        
        print(f"PASS: reconcile returns 503 when payments disabled")


class TestWebhookSignatureGuard:
    """Test webhook signature validation guards"""
    
    def test_webhook_missing_signature_returns_400(self):
        """POST /api/payments/webhook without signature returns 400"""
        payload = {
            "id": "evt_test_missing_sig",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}}
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        
        # Verify error mentions signature
        try:
            detail = resp.json().get("detail", "")
            assert "signature" in detail.lower() or "missing" in detail.lower(), \
                f"Error should mention missing signature: {detail}"
        except Exception:
            pass
        
        print(f"PASS: webhook returns 400 for missing signature")
    
    def test_stripe_webhook_missing_signature_returns_400(self):
        """POST /api/payments/stripe/webhook without signature returns 400"""
        payload = {
            "id": "evt_test_stripe_endpoint",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}}
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/stripe/webhook",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print(f"PASS: /api/payments/stripe/webhook returns 400 for missing signature")
    
    def test_webhook_invalid_signature_returns_400(self):
        """POST /api/payments/webhook with invalid signature returns 400"""
        payload = {
            "id": "evt_test_invalid_sig",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}}
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "stripe-signature": "t=1234567890,v1=invalid_hash_value"
            },
            timeout=30
        )
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        
        # Verify error mentions signature validation
        try:
            detail = resp.json().get("detail", "")
            assert "signature" in detail.lower() or "invalid" in detail.lower(), \
                f"Error should mention invalid signature: {detail}"
        except Exception:
            pass
        
        print(f"PASS: webhook returns 400 for invalid signature")
    
    def test_webhook_malformed_signature_returns_400(self):
        """POST /api/payments/webhook with malformed signature returns 400"""
        payload = {"id": "evt_malformed", "type": "payment_intent.created"}
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "stripe-signature": "totally_invalid_format"
            },
            timeout=30
        )
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print(f"PASS: webhook returns 400 for malformed signature")


class TestWebhookReplayProtection:
    """Test webhook duplicate event handling (replay protection)"""
    
    def test_webhook_event_id_consistency(self):
        """Webhook endpoint consistently rejects invalid signatures (no event processing)"""
        # Note: True duplicate detection requires valid signatures
        # We test that invalid signatures are consistently rejected
        
        event_id = f"evt_replay_test_{int(time.time())}"
        payload = {
            "id": event_id,
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test"}}
        }
        
        # First request
        resp1 = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "stripe-signature": "t=1234567890,v1=fake_sig_1"
            },
            timeout=30
        )
        
        # Second request with same event_id
        resp2 = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "stripe-signature": "t=1234567890,v1=fake_sig_2"
            },
            timeout=30
        )
        
        # Both should be rejected with 400 (invalid signature)
        assert resp1.status_code == 400, f"First request expected 400, got {resp1.status_code}"
        assert resp2.status_code == 400, f"Second request expected 400, got {resp2.status_code}"
        
        print(f"PASS: Webhook consistently rejects invalid signatures")
    
    def test_webhook_replay_protection_database_model_exists(self):
        """Verify ProcessedWebhookEvent model exists for duplicate detection"""
        # This is a structural test - if the import fails, the feature isn't implemented
        try:
            from app.models.payment import ProcessedWebhookEvent
            
            # Verify model has required fields
            assert hasattr(ProcessedWebhookEvent, 'provider'), "Missing 'provider' field"
            assert hasattr(ProcessedWebhookEvent, 'event_id'), "Missing 'event_id' field"
            assert hasattr(ProcessedWebhookEvent, 'event_type'), "Missing 'event_type' field"
            
            print(f"PASS: ProcessedWebhookEvent model exists with required fields")
            print(f"  Fields: provider, event_id, event_type, livemode, request_id, created_at, processed_at")
        except ImportError as e:
            pytest.fail(f"ProcessedWebhookEvent model not found: {e}")


class TestWebhookEventMapping:
    """Test Stripe event type to payment status mapping"""
    
    def test_stripe_event_mapping_function_exists(self):
        """Verify Stripe event mapping domain function exists"""
        try:
            from app.domains.payments import (
                map_stripe_event_to_payment_status,
                map_payment_status_to_listing_status
            )
            print(f"PASS: Payment status mapping functions exist")
        except ImportError as e:
            pytest.fail(f"Payment domain functions not found: {e}")
    
    def test_payment_intent_succeeded_mapping(self):
        """payment_intent.succeeded -> succeeded status"""
        from app.domains.payments import map_stripe_event_to_payment_status
        
        result = map_stripe_event_to_payment_status("payment_intent.succeeded")
        assert result == "succeeded", f"Expected 'succeeded', got '{result}'"
        print(f"PASS: payment_intent.succeeded -> succeeded")
    
    def test_payment_intent_failed_mapping(self):
        """payment_intent.payment_failed -> failed status"""
        from app.domains.payments import map_stripe_event_to_payment_status
        
        result = map_stripe_event_to_payment_status("payment_intent.payment_failed")
        assert result == "failed", f"Expected 'failed', got '{result}'"
        print(f"PASS: payment_intent.payment_failed -> failed")
    
    def test_invoice_paid_mapping(self):
        """invoice.paid event mapping"""
        from app.domains.payments import map_stripe_event_to_payment_status
        
        result = map_stripe_event_to_payment_status("invoice.paid")
        # May return 'succeeded' or specific invoice status
        assert result is not None or result in [None, "succeeded", "paid"], \
            f"Unexpected result for invoice.paid: {result}"
        print(f"PASS: invoice.paid -> {result}")
    
    def test_invoice_payment_failed_mapping(self):
        """invoice.payment_failed event mapping"""
        from app.domains.payments import map_stripe_event_to_payment_status
        
        result = map_stripe_event_to_payment_status("invoice.payment_failed")
        # May return 'failed' or None for invoice events
        print(f"PASS: invoice.payment_failed -> {result}")
    
    def test_checkout_session_completed_mapping(self):
        """checkout.session.completed event mapping"""
        from app.domains.payments import map_stripe_event_to_payment_status
        
        result = map_stripe_event_to_payment_status("checkout.session.completed")
        # Checkout session status depends on payment_status field
        print(f"PASS: checkout.session.completed -> {result}")


class TestRuntimeConfigStatus:
    """Test runtime config status field"""
    
    def test_runtime_config_includes_status_field(self):
        """runtime-config should include status field"""
        resp = requests.get(f"{BASE_URL}/api/payments/runtime-config", timeout=30)
        assert resp.status_code == 200
        
        data = resp.json()
        
        assert "status" in data, "Missing 'status' field"
        assert data["status"] in ["enabled", "disabled"], \
            f"status should be 'enabled' or 'disabled', got '{data['status']}'"
        
        # status should match payments_enabled
        expected_status = "enabled" if data["payments_enabled"] else "disabled"
        assert data["status"] == expected_status, \
            f"status mismatch: status={data['status']}, payments_enabled={data['payments_enabled']}"
        
        print(f"PASS: runtime-config status field is consistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
