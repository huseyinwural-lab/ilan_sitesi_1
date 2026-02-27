"""
P2 Alerting & Legacy Cleanup Tests
Covers:
1. Alerting secret checklist endpoint
2. Channel-based secret presence
3. Channel-based simulation payload
4. Channel-based audit filter
5. Legacy publish physical removal (404)
6. Legacy usage endpoint removal (404)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for testing"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"}
    )
    if response.status_code != 200:
        pytest.skip("Admin login failed - skipping authenticated tests")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin auth headers"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer token for testing (should be blocked from admin endpoints)"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "dealer1772201722@example.com", "password": "Dealer123!"}
    )
    if response.status_code != 200:
        pytest.skip("Dealer login failed - skipping dealer tests")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def dealer_headers(dealer_token):
    """Dealer auth headers"""
    return {"Authorization": f"Bearer {dealer_token}", "Content-Type": "application/json"}


class TestAlertingSecretChecklist:
    """Test: GET /api/admin/ui/configs/dashboard/ops-alerts/secret-checklist"""

    def test_secret_checklist_returns_200(self, admin_headers):
        """Secret checklist endpoint should return 200 with channel info"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-checklist",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "channels" in data, "Response should contain 'channels' key"
        channels = data["channels"]
        
        # Validate all 3 channels present
        assert "smtp" in channels, "SMTP channel should be present"
        assert "slack" in channels, "Slack channel should be present"
        assert "pagerduty" in channels, "PagerDuty channel should be present"
        
        # Validate SMTP structure
        smtp = channels["smtp"]
        assert "required_secrets" in smtp, "SMTP should have required_secrets"
        assert "formats" in smtp, "SMTP should have formats"
        assert "used_in" in smtp, "SMTP should have used_in"
        assert "test_payload" in smtp, "SMTP should have test_payload"
        assert smtp["used_in"] == "_simulate_smtp_delivery"
        
        # Validate Slack structure
        slack = channels["slack"]
        assert "required_secrets" in slack
        assert "ALERT_SLACK_WEBHOOK_URL" in slack["formats"]
        
        # Validate PagerDuty structure
        pd = channels["pagerduty"]
        assert "required_secrets" in pd
        assert "ALERT_PAGERDUTY_ROUTING_KEY" in pd["formats"]
        
        # Validate dry_run_scenario
        assert "dry_run_scenario" in data, "Response should contain dry_run_scenario"
        assert len(data["dry_run_scenario"]) >= 3, "Should have multiple dry run steps"
        
        print(f"Secret checklist: {len(channels)} channels with dry_run_scenario steps")

    def test_secret_checklist_requires_auth(self):
        """Secret checklist should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-checklist"
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"

    def test_secret_checklist_blocks_dealer(self, dealer_headers):
        """Secret checklist should block dealer role"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-checklist",
            headers=dealer_headers
        )
        assert response.status_code in [401, 403], f"Expected 401/403 for dealer, got {response.status_code}"


class TestChannelBasedSecretPresence:
    """Test: GET /api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=..."""

    def test_secret_presence_smtp_only(self, admin_headers):
        """Secret presence for SMTP channel only"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=smtp",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "ops_alerts_secret_presence" in data
        presence = data["ops_alerts_secret_presence"]
        
        assert "status" in presence, "Should have status field"
        assert presence["status"] in ["READY", "BLOCKED"], f"Invalid status: {presence['status']}"
        assert "channels" in presence, "Should have channels field"
        assert "smtp" in presence["channels"], "SMTP channel should be in response"
        assert "requested_channels" in presence
        assert "smtp" in presence["requested_channels"]
        
        smtp_info = presence["channels"]["smtp"]
        assert "status" in smtp_info, "SMTP should have status"
        assert smtp_info["status"] in ["ENABLED", "DISABLED"]
        
        print(f"SMTP secret presence: status={presence['status']}, smtp_status={smtp_info['status']}")

    def test_secret_presence_slack_only(self, admin_headers):
        """Secret presence for Slack channel only"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=slack",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        presence = data["ops_alerts_secret_presence"]
        assert "slack" in presence["channels"]
        assert "requested_channels" in presence
        assert "slack" in presence["requested_channels"]
        
        slack_info = presence["channels"]["slack"]
        assert "status" in slack_info
        assert "target_channel_verified" in slack_info
        
        print(f"Slack secret presence: status={presence['status']}, slack_status={slack_info['status']}")

    def test_secret_presence_pagerduty_only(self, admin_headers):
        """Secret presence for PagerDuty channel only"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=pagerduty",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        presence = data["ops_alerts_secret_presence"]
        assert "pagerduty" in presence["channels"]
        assert "requested_channels" in presence
        assert "pagerduty" in presence["requested_channels"]
        
        print(f"PagerDuty secret presence: status={presence['status']}")

    def test_secret_presence_multiple_channels(self, admin_headers):
        """Secret presence for multiple channels"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=smtp,slack",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        presence = data["ops_alerts_secret_presence"]
        assert "smtp" in presence["channels"]
        assert "slack" in presence["channels"]
        # PagerDuty should NOT be in channels if not requested
        
        print(f"Multi-channel presence: requested={presence['requested_channels']}")

    def test_secret_presence_invalid_channel(self, admin_headers):
        """Secret presence with invalid channel should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/secret-presence?channels=invalid_channel",
            headers=admin_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid channel, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert "INVALID_CHANNEL_SELECTION" in str(detail.get("code", "")) or "invalid" in str(detail).lower()
        
        print(f"Invalid channel error: {detail}")


class TestChannelBasedSimulation:
    """Test: POST /api/admin/ops/alert-delivery/rerun-simulation with channels"""

    def test_simulation_with_smtp_channel(self, admin_headers):
        """Simulation with SMTP channel only"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard", "channels": ["smtp"]}
        )
        # Can be 200 (success) or 429 (rate limited)
        assert response.status_code in [200, 429], f"Expected 200/429, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "correlation_id" in data, "Should have correlation_id"
            assert "delivery_status" in data, "Should have delivery_status"
            assert "channels_requested" in data, "Should have channels_requested"
            assert "smtp" in data.get("channels_requested", [])
            print(f"SMTP simulation: correlation_id={data['correlation_id']}, status={data['delivery_status']}")
        else:
            data = response.json()
            assert "retry_after_seconds" in str(data) or "rate" in str(data).lower()
            print(f"Rate limited: {data}")

    def test_simulation_with_slack_channel(self, admin_headers):
        """Simulation with Slack channel only"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard", "channels": ["slack"]}
        )
        assert response.status_code in [200, 429]
        
        if response.status_code == 200:
            data = response.json()
            assert "slack" in data.get("channels_requested", [])
            print(f"Slack simulation: status={data.get('delivery_status')}")

    def test_simulation_with_pagerduty_channel(self, admin_headers):
        """Simulation with PagerDuty channel only"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard", "channels": ["pagerduty"]}
        )
        assert response.status_code in [200, 429]
        
        if response.status_code == 200:
            data = response.json()
            assert "pagerduty" in data.get("channels_requested", [])
            print(f"PagerDuty simulation: status={data.get('delivery_status')}")

    def test_simulation_invalid_channel(self, admin_headers):
        """Simulation with invalid channel should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard", "channels": ["invalid"]}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestChannelBasedAuditFilter:
    """Test: GET /api/admin/ui/configs/dashboard/ops-alerts/delivery-audit with channel filter"""

    def test_audit_default_returns_200(self, admin_headers):
        """Audit endpoint should return 200 with default params"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "items" in data, "Should have items array"
        assert "total_records" in data, "Should have total_records"
        
        print(f"Audit default: total_records={data['total_records']}, items={len(data['items'])}")

    def test_audit_with_smtp_channel_filter(self, admin_headers):
        """Audit with SMTP channel filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?channels=smtp",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are items, they should all be SMTP
        for item in data.get("items", []):
            channel = item.get("channel")
            if channel:
                assert channel == "smtp", f"Expected smtp channel, got {channel}"
        
        print(f"SMTP audit filter: {len(data.get('items', []))} records")

    def test_audit_with_slack_channel_filter(self, admin_headers):
        """Audit with Slack channel filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?channels=slack",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for item in data.get("items", []):
            channel = item.get("channel")
            if channel:
                assert channel == "slack", f"Expected slack channel, got {channel}"
        
        print(f"Slack audit filter: {len(data.get('items', []))} records")

    def test_audit_with_pagerduty_channel_filter(self, admin_headers):
        """Audit with PagerDuty channel filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?channels=pagerduty",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for item in data.get("items", []):
            channel = item.get("channel")
            if channel:
                assert channel == "pagerduty", f"Expected pagerduty channel, got {channel}"
        
        print(f"PagerDuty audit filter: {len(data.get('items', []))} records")

    def test_audit_with_correlation_id_and_channel(self, admin_headers):
        """Audit with both correlation_id and channel filter"""
        # First get any existing correlation_id
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?limit=1",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("items") and len(data["items"]) > 0:
            correlation_id = data["items"][0].get("correlation_id")
            if correlation_id:
                # Test with correlation_id + channel filter
                response2 = requests.get(
                    f"{BASE_URL}/api/admin/ui/configs/dashboard/ops-alerts/delivery-audit?correlation_id={correlation_id}&channels=smtp",
                    headers=admin_headers
                )
                assert response2.status_code == 200
                data2 = response2.json()
                
                # All items should match the correlation_id
                for item in data2.get("items", []):
                    assert item.get("correlation_id") == correlation_id
                
                print(f"Audit with correlation_id filter: {len(data2.get('items', []))} records")
        else:
            print("No audit records found for correlation_id test")


class TestLegacyPublishRemoval:
    """Test: Legacy publish endpoint should return 404"""

    def test_legacy_publish_returns_404(self, admin_headers):
        """POST /api/admin/ui/configs/dashboard/publish/{config_id} should return 404"""
        # Test with a dummy config_id
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
            json={}
        )
        assert response.status_code == 404, f"Expected 404 for legacy publish, got {response.status_code}: {response.text}"
        print(f"Legacy publish correctly returns 404")

    def test_legacy_publish_with_any_config_id(self, admin_headers):
        """Legacy publish with any config_id should return 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/publish/test-config-id",
            headers=admin_headers,
            json={}
        )
        # Should be 404 or 422 (validation error) - either way, the route should not exist
        assert response.status_code in [404, 422], f"Expected 404/422 for legacy publish, got {response.status_code}"
        print(f"Legacy publish with test id returns {response.status_code}")


class TestLegacyUsageRemoval:
    """Test: Legacy usage endpoint should return 404"""

    def test_legacy_usage_returns_404(self, admin_headers):
        """GET /api/admin/ui/configs/dashboard/legacy-usage should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/legacy-usage",
            headers=admin_headers
        )
        assert response.status_code == 404, f"Expected 404 for legacy-usage, got {response.status_code}: {response.text}"
        print(f"Legacy usage correctly returns 404")

    def test_legacy_usage_with_params_returns_404(self, admin_headers):
        """GET /api/admin/ui/configs/dashboard/legacy-usage?days=30 should return 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/dashboard/legacy-usage?days=30",
            headers=admin_headers
        )
        assert response.status_code == 404, f"Expected 404 for legacy-usage with params, got {response.status_code}"
        print(f"Legacy usage with params correctly returns 404")


class TestAlertDeliveryMetrics:
    """Test: GET /api/admin/ops/alert-delivery-metrics"""

    def test_metrics_returns_200(self, admin_headers):
        """Alert delivery metrics should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate expected fields
        assert "success_rate" in data or "total_attempts" in data
        print(f"Alert metrics: {data}")

    def test_metrics_requires_auth(self):
        """Alert metrics should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h"
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
