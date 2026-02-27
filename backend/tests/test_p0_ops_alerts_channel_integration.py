"""
P0 Ops Alert Channel Integration Tests
- GET /api/admin/ui/configs/{config_type}/ops-alerts/secret-presence
- POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate
- GET /api/admin/ui/configs/{config_type}/ops-alerts/delivery-audit

Tests verify:
1. Secret presence endpoint returns proper structure with ENABLED/DISABLED channels
2. Simulate endpoint returns blocked_missing_secrets when secrets are missing
3. Simulate endpoint returns channel_results when secrets are present
4. Delivery audit endpoint filters by correlation_id
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


def _admin_token() -> str:
    """Authenticate admin user and return access token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"X-Portal-Scope": "admin"},
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text[:200]}")
    payload = response.json()
    return payload.get("access_token") or payload.get("token")


def _headers(token: str):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_token() -> str:
    return _admin_token()


class TestSecretPresenceEndpoint:
    """GET /api/admin/ui/configs/{config_type}/ops-alerts/secret-presence tests"""

    def test_secret_presence_returns_ops_alerts_structure(self, admin_token: str):
        """Verify ops_alerts_secret_presence structure exists in response"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        payload = response.json()
        assert "ops_alerts_secret_presence" in payload, f"Missing ops_alerts_secret_presence key: {payload}"
        
        secret_presence = payload["ops_alerts_secret_presence"]
        
        # Verify top-level structure
        assert "status" in secret_presence, f"Missing 'status' in secret_presence: {secret_presence}"
        assert secret_presence["status"] in ["READY", "BLOCKED"], f"Invalid status: {secret_presence['status']}"
        
        assert "missing_keys" in secret_presence, f"Missing 'missing_keys': {secret_presence}"
        assert isinstance(secret_presence["missing_keys"], list), f"missing_keys should be a list"
        
        assert "channels" in secret_presence, f"Missing 'channels': {secret_presence}"
        
    def test_secret_presence_channels_have_status_field(self, admin_token: str):
        """Verify each channel has ENABLED/DISABLED status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        secret_presence = response.json()["ops_alerts_secret_presence"]
        channels = secret_presence["channels"]
        
        # Verify expected channels exist
        assert "slack" in channels, f"Missing 'slack' channel: {channels}"
        assert "smtp" in channels, f"Missing 'smtp' channel: {channels}"
        assert "pagerduty" in channels, f"Missing 'pagerduty' channel: {channels}"
        
        # Verify each channel has status and missing_keys
        for channel_name in ["slack", "smtp", "pagerduty"]:
            channel = channels[channel_name]
            assert "status" in channel, f"Missing 'status' in {channel_name}: {channel}"
            assert channel["status"] in ["ENABLED", "DISABLED"], f"Invalid status for {channel_name}: {channel['status']}"
            assert "missing_keys" in channel, f"Missing 'missing_keys' in {channel_name}: {channel}"
            assert isinstance(channel["missing_keys"], list), f"missing_keys should be list for {channel_name}"
            
    def test_secret_presence_slack_channel_fields(self, admin_token: str):
        """Verify slack channel has target_channel_verified field"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        slack = response.json()["ops_alerts_secret_presence"]["channels"]["slack"]
        assert "target_channel_verified" in slack, f"Missing target_channel_verified in slack: {slack}"
        
    def test_secret_presence_smtp_channel_fields(self, admin_token: str):
        """Verify smtp channel has recipient_list_configured and recipient_count"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        smtp = response.json()["ops_alerts_secret_presence"]["channels"]["smtp"]
        assert "recipient_list_configured" in smtp, f"Missing recipient_list_configured in smtp: {smtp}"
        assert "recipient_count" in smtp, f"Missing recipient_count in smtp: {smtp}"
        
    def test_secret_presence_works_for_header_config_type(self, admin_token: str):
        """Verify endpoint works for different config types"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert "ops_alerts_secret_presence" in response.json()


class TestSimulateEndpoint:
    """POST /api/admin/ui/configs/{config_type}/ops-alerts/simulate tests"""

    def test_simulate_returns_required_fields(self, admin_token: str):
        """Verify simulate response has all required fields"""
        correlation_id = f"test-sim-{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "correlation_id": correlation_id,
                "avg_lock_wait_ms": 100,
                "max_lock_wait_ms": 200,
                "publish_duration_ms_p95": 500,
                "conflict_rate": 15,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        payload = response.json()
        
        # Verify required fields
        assert "delivery_status" in payload, f"Missing delivery_status: {payload}"
        assert "correlation_id" in payload, f"Missing correlation_id: {payload}"
        assert "alerts" in payload, f"Missing alerts: {payload}"
        assert "ops_alerts_secret_presence" in payload, f"Missing ops_alerts_secret_presence: {payload}"
        assert "sample_metrics" in payload, f"Missing sample_metrics: {payload}"
        
    def test_simulate_correlation_id_returned(self, admin_token: str):
        """Verify correlation_id is returned in response"""
        correlation_id = f"test-corr-{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "correlation_id": correlation_id,
                "avg_lock_wait_ms": 50,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["correlation_id"] == correlation_id
        
    def test_simulate_generates_correlation_id_if_not_provided(self, admin_token: str):
        """Verify correlation_id is auto-generated if not provided"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 50,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        assert response.json()["correlation_id"] is not None
        assert len(response.json()["correlation_id"]) > 0
        
    def test_simulate_blocked_missing_secrets_when_secrets_absent(self, admin_token: str):
        """Verify blocked_missing_secrets status when secrets are not configured"""
        # First check if secrets are missing
        presence_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        secret_presence = presence_response.json()["ops_alerts_secret_presence"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 300,
                "max_lock_wait_ms": 500,
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        
        payload = response.json()
        
        # If secrets are BLOCKED, expect blocked_missing_secrets
        if secret_presence["status"] == "BLOCKED":
            assert payload["delivery_status"] == "blocked_missing_secrets", \
                f"Expected blocked_missing_secrets, got: {payload['delivery_status']}"
            assert "fail_fast" in payload, f"Missing fail_fast when secrets blocked: {payload}"
            assert payload["fail_fast"] is not None
            assert "missing_keys" in payload["fail_fast"], f"Missing missing_keys in fail_fast: {payload['fail_fast']}"
            assert len(payload["fail_fast"]["missing_keys"]) > 0
        else:
            # Secrets are ready, expect ok or partial_fail
            assert payload["delivery_status"] in ["ok", "partial_fail"], \
                f"Unexpected delivery_status: {payload['delivery_status']}"
            assert payload["fail_fast"] is None
            
    def test_simulate_fail_fast_contains_missing_keys(self, admin_token: str):
        """Verify fail_fast.missing_keys matches secret presence missing_keys"""
        # First get secret presence
        presence_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        secret_presence = presence_response.json()["ops_alerts_secret_presence"]
        
        if secret_presence["status"] == "READY":
            pytest.skip("Secrets are configured - cannot test blocked scenario")
            
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={"avg_lock_wait_ms": 100},
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        
        fail_fast = response.json()["fail_fast"]
        assert fail_fast is not None
        assert set(fail_fast["missing_keys"]) == set(secret_presence["missing_keys"])
        
    def test_simulate_alerts_generated_for_critical_metrics(self, admin_token: str):
        """Verify alerts are generated when metrics exceed critical thresholds"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 300,      # > 220 critical threshold
                "max_lock_wait_ms": 500,      # > 450 critical threshold
                "publish_duration_ms_p95": 2000,  # > 1700 critical threshold
                "conflict_rate": 50,          # > 40 critical threshold
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        
        alerts = response.json()["alerts"]
        assert isinstance(alerts, list)
        
        # Verify critical alerts are generated
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        assert len(critical_alerts) >= 3, f"Expected at least 3 critical alerts, got: {critical_alerts}"
        
        # Check for specific metrics
        alert_metrics = [a["metric"] for a in critical_alerts]
        assert "avg_lock_wait_ms" in alert_metrics, "Missing avg_lock_wait_ms critical alert"
        assert "max_lock_wait_ms" in alert_metrics, "Missing max_lock_wait_ms critical alert"
        
    def test_simulate_alerts_generated_for_warning_metrics(self, admin_token: str):
        """Verify warning alerts are generated for warning-level metrics"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "avg_lock_wait_ms": 150,      # > 120 warning threshold
                "max_lock_wait_ms": 300,      # > 250 warning threshold
                "publish_duration_ms_p95": 1200,  # > 1000 warning threshold
                "conflict_rate": 30,          # > 25 warning threshold
            },
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        
        alerts = response.json()["alerts"]
        warning_alerts = [a for a in alerts if a.get("severity") == "warning"]
        assert len(warning_alerts) >= 3, f"Expected at least 3 warning alerts, got: {alerts}"
        
    def test_simulate_channel_results_when_secrets_ready(self, admin_token: str):
        """If secrets are ready, verify channel_results structure"""
        presence_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        secret_presence = presence_response.json()["ops_alerts_secret_presence"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={"avg_lock_wait_ms": 100},
            headers=_headers(admin_token),
        )
        assert response.status_code == 200
        
        payload = response.json()
        channel_results = payload.get("channel_results") or {}
        
        if secret_presence["status"] == "READY":
            # Expect channel results when secrets are configured
            assert "slack" in channel_results, f"Missing slack in channel_results: {channel_results}"
            assert "smtp" in channel_results, f"Missing smtp in channel_results: {channel_results}"
            assert "pagerduty" in channel_results, f"Missing pagerduty in channel_results: {channel_results}"
            
            # Verify slack structure
            slack = channel_results["slack"]
            assert "delivery_status" in slack, f"Missing delivery_status in slack: {slack}"
            assert "retry_backoff_log" in slack, f"Missing retry_backoff_log in slack: {slack}"
            
            # Verify smtp structure
            smtp = channel_results["smtp"]
            assert "delivery_status" in smtp, f"Missing delivery_status in smtp: {smtp}"
            assert "recipient_count" in smtp, f"Missing recipient_count in smtp: {smtp}"
            
            # Verify pagerduty structure
            pagerduty = channel_results["pagerduty"]
            assert "delivery_status" in pagerduty, f"Missing delivery_status in pagerduty: {pagerduty}"
        else:
            # When blocked, channel_results should be empty
            assert channel_results == {}, f"Expected empty channel_results when blocked: {channel_results}"


class TestDeliveryAuditEndpoint:
    """GET /api/admin/ui/configs/{config_type}/ops-alerts/delivery-audit tests"""

    def test_delivery_audit_returns_structure(self, admin_token: str):
        """Verify delivery-audit endpoint returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        
        payload = response.json()
        
        # Verify structure
        assert "items" in payload, f"Missing items: {payload}"
        assert isinstance(payload["items"], list)
        assert "total_records" in payload, f"Missing total_records: {payload}"
        assert "channels_logged" in payload, f"Missing channels_logged: {payload}"
        
    def test_delivery_audit_filters_by_correlation_id(self, admin_token: str):
        """Verify delivery-audit filters items by correlation_id"""
        # First run a simulate to create audit records
        correlation_id = f"test-audit-{uuid.uuid4().hex[:8]}"
        requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "correlation_id": correlation_id,
                "avg_lock_wait_ms": 100,
            },
            headers=_headers(admin_token),
        )
        
        # Query delivery audit with correlation_id
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?correlation_id={correlation_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        payload = response.json()
        
        # Verify correlation_id matches
        assert payload.get("correlation_id") == correlation_id, \
            f"Expected correlation_id={correlation_id}, got: {payload.get('correlation_id')}"
        
        # All items should have matching correlation_id
        for item in payload["items"]:
            assert item.get("correlation_id") == correlation_id, \
                f"Item has wrong correlation_id: {item.get('correlation_id')}"
                
    def test_delivery_audit_item_structure(self, admin_token: str):
        """Verify each audit item has expected fields"""
        # First run a simulate
        correlation_id = f"test-item-{uuid.uuid4().hex[:8]}"
        requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "correlation_id": correlation_id,
                "avg_lock_wait_ms": 100,
            },
            headers=_headers(admin_token),
        )
        
        # Get audit records - may have items if secrets were ready
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?correlation_id={correlation_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        # If there are items, verify structure
        items = response.json()["items"]
        if items:
            item = items[0]
            expected_fields = [
                "audit_id", "created_at", "actor_email", "correlation_id",
                "channel", "delivery_status", "retry_backoff_log"
            ]
            for field in expected_fields:
                assert field in item, f"Missing {field} in audit item: {item}"
                
    def test_delivery_audit_respects_limit_parameter(self, admin_token: str):
        """Verify limit parameter is respected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?limit=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        items = response.json()["items"]
        assert len(items) <= 5, f"Expected at most 5 items, got: {len(items)}"
        
    def test_delivery_audit_returns_latest_correlation_if_not_specified(self, admin_token: str):
        """When no correlation_id provided, should return latest correlation's records"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        
        payload = response.json()
        
        # If items exist, all should share same correlation_id
        items = payload["items"]
        if items:
            first_correlation = items[0].get("correlation_id")
            for item in items:
                assert item.get("correlation_id") == first_correlation, \
                    f"Inconsistent correlation_ids in response"


class TestEndToEndSimulationFlow:
    """End-to-end test for simulate -> delivery-audit flow"""

    def test_simulate_creates_audit_records_that_can_be_queried(self, admin_token: str):
        """Full flow: simulate -> query audit -> verify records"""
        # Step 1: Get secret presence
        presence_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert presence_response.status_code == 200
        secret_presence = presence_response.json()["ops_alerts_secret_presence"]
        
        # Step 2: Run simulate
        correlation_id = f"e2e-test-{uuid.uuid4().hex[:8]}"
        simulate_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/simulate",
            json={
                "correlation_id": correlation_id,
                "avg_lock_wait_ms": 250,
                "max_lock_wait_ms": 400,
                "publish_duration_ms_p95": 1500,
                "conflict_rate": 35,
            },
            headers=_headers(admin_token),
        )
        assert simulate_response.status_code == 200
        simulate_result = simulate_response.json()
        
        # Step 3: Verify simulate response
        assert simulate_result["correlation_id"] == correlation_id
        
        if secret_presence["status"] == "BLOCKED":
            assert simulate_result["delivery_status"] == "blocked_missing_secrets"
            assert simulate_result["fail_fast"] is not None
        else:
            assert simulate_result["delivery_status"] in ["ok", "partial_fail"]
            assert simulate_result["channel_results"] != {}
            
        # Step 4: Query delivery audit
        audit_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?correlation_id={correlation_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert audit_response.status_code == 200
        
        audit_result = audit_response.json()
        assert audit_result["correlation_id"] == correlation_id
        
        # If secrets were ready and delivery happened, expect audit records
        if secret_presence["status"] == "READY":
            assert len(audit_result["items"]) > 0, "Expected audit records when secrets are ready"
            assert "slack" in audit_result["channels_logged"] or \
                   "smtp" in audit_result["channels_logged"] or \
                   "pagerduty" in audit_result["channels_logged"], \
                   f"Expected at least one channel logged: {audit_result['channels_logged']}"
