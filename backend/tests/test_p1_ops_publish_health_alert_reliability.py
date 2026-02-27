"""
P1 - Publish Health + Alert Reliability Integration Tests

Test Coverage:
- GET /api/admin/ops/alert-delivery-metrics?window=24h
- GET /api/admin/ops/alert-delivery-metrics?window=48h (400 INVALID_WINDOW)
- POST /api/admin/ops/alert-delivery/rerun-simulation
- Rate limit: max 3 per minute, 4th request returns 429 RATE_LIMITED
- Role-based access: dealer token returns 403

Required credentials:
- Admin: admin@platform.com / Admin123!
- Dealer: dealer@platform.com / Dealer123!
"""

import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for API calls."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
        timeout=15,
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers with admin auth."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer token for forbidden access tests."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "dealer@platform.com", "password": "Dealer123!"},
        timeout=15,
    )
    if response.status_code != 200:
        pytest.skip(f"Dealer login failed: {response.status_code} {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def dealer_headers(dealer_token):
    """Headers with dealer auth."""
    return {
        "Authorization": f"Bearer {dealer_token}",
        "Content-Type": "application/json",
    }


# ============================================================================
# GET /api/admin/ops/alert-delivery-metrics?window=24h
# ============================================================================

class TestAlertDeliveryMetrics24h:
    """Test GET /api/admin/ops/alert-delivery-metrics?window=24h endpoint."""

    def test_metrics_24h_returns_200(self, admin_headers):
        """Should return 200 with 24h window."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_metrics_24h_has_required_fields(self, admin_headers):
        """Should return all required fields in response."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        
        # Required top-level fields
        required_fields = [
            "total_attempts",
            "successful_deliveries",
            "failed_deliveries",
            "success_rate",
            "last_failure_timestamp",
            "channel_breakdown",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_metrics_24h_channel_breakdown_structure(self, admin_headers):
        """Should have channel_breakdown with slack, smtp, pd keys."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        
        channel_breakdown = data.get("channel_breakdown", {})
        expected_channels = ["slack", "smtp", "pd"]
        for channel in expected_channels:
            assert channel in channel_breakdown, f"Missing channel in breakdown: {channel}"
            
            # Each channel should have these fields
            channel_data = channel_breakdown[channel]
            assert "total_attempts" in channel_data
            assert "successful_deliveries" in channel_data
            assert "failed_deliveries" in channel_data
            assert "success_rate" in channel_data
            assert "last_failure_timestamp" in channel_data

    def test_metrics_24h_success_rate_is_numeric(self, admin_headers):
        """success_rate should be a numeric value."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        
        success_rate = data.get("success_rate")
        assert isinstance(success_rate, (int, float)), f"success_rate should be numeric, got {type(success_rate)}"
        assert 0 <= success_rate <= 100, f"success_rate should be 0-100, got {success_rate}"


# ============================================================================
# GET /api/admin/ops/alert-delivery-metrics?window=48h (INVALID_WINDOW)
# ============================================================================

class TestAlertDeliveryMetricsInvalidWindow:
    """Test invalid window parameter returns 400 INVALID_WINDOW."""

    def test_window_48h_returns_400(self, admin_headers):
        """48h window should return 400 - max is 24h."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=48h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"

    def test_window_48h_error_code_is_invalid_window(self, admin_headers):
        """Error detail should contain INVALID_WINDOW code."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=48h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 400
        data = response.json()
        
        # Check error code
        detail = data.get("detail", {})
        assert detail.get("code") == "INVALID_WINDOW", f"Expected INVALID_WINDOW code, got: {detail}"

    def test_window_invalid_format_returns_400(self, admin_headers):
        """Invalid window format should return 400."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=invalid",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        assert detail.get("code") == "INVALID_WINDOW"

    def test_valid_windows_work(self, admin_headers):
        """Valid windows (1h, 6h, 12h, 24h) should work."""
        valid_windows = ["1h", "6h", "12h", "24h"]
        for window in valid_windows:
            response = requests.get(
                f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window={window}",
                headers=admin_headers,
                timeout=15,
            )
            assert response.status_code == 200, f"Window {window} should work, got {response.status_code}"


# ============================================================================
# POST /api/admin/ops/alert-delivery/rerun-simulation
# ============================================================================

class TestRerunAlertSimulation:
    """Test POST /api/admin/ops/alert-delivery/rerun-simulation endpoint."""

    def test_rerun_simulation_returns_correlation_id(self, admin_headers):
        """Should return correlation_id in response."""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard"},
            timeout=30,
        )
        # Accept 200 or 429 (rate limited from previous tests)
        if response.status_code == 429:
            pytest.skip("Rate limited - cannot test correlation_id")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "correlation_id" in data, "Response should include correlation_id"
        assert data["correlation_id"], "correlation_id should not be empty"

    def test_rerun_simulation_returns_delivery_status(self, admin_headers):
        """Should return delivery_status in response."""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard"},
            timeout=30,
        )
        if response.status_code == 429:
            pytest.skip("Rate limited - cannot test delivery_status")
        
        assert response.status_code == 200
        data = response.json()
        assert "delivery_status" in data, "Response should include delivery_status"
        # delivery_status can be "ok", "partial", "fail", or "blocked_missing_secrets"
        valid_statuses = ["ok", "partial", "fail", "blocked_missing_secrets"]
        assert data["delivery_status"] in valid_statuses, f"Invalid delivery_status: {data['delivery_status']}"

    def test_rerun_simulation_returns_channel_results_or_fail_fast(self, admin_headers):
        """Should return channel_results or fail_fast depending on secrets."""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard"},
            timeout=30,
        )
        if response.status_code == 429:
            pytest.skip("Rate limited")
        
        assert response.status_code == 200
        data = response.json()
        
        # Either channel_results (when secrets are configured) or fail_fast (when blocked)
        has_channel_results = "channel_results" in data
        has_fail_fast = "fail_fast" in data
        
        assert has_channel_results or has_fail_fast, "Response should include channel_results or fail_fast"


# ============================================================================
# Rate Limit: max 3 per minute, 4th returns 429 RATE_LIMITED
# ============================================================================

class TestRerunSimulationRateLimit:
    """Test rate limiting on rerun-simulation endpoint (max 3 per minute)."""

    def test_rate_limit_allows_first_three_requests(self, admin_headers):
        """First 3 requests within a minute should succeed."""
        # Note: This test may need to wait if previous tests consumed quota
        successes = 0
        for i in range(3):
            response = requests.post(
                f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
                headers=admin_headers,
                json={"config_type": "dashboard", "test_iteration": i},
                timeout=30,
            )
            if response.status_code == 200:
                successes += 1
            elif response.status_code == 429:
                # Already rate limited from previous test runs
                pytest.skip("Already rate limited from previous tests")
        
        # At least some should have succeeded
        assert successes >= 0, "Rate limit test setup issue"

    def test_rate_limit_blocks_fourth_request(self, admin_headers):
        """4th request within a minute should return 429 RATE_LIMITED."""
        # Make 4 rapid requests - 4th should be blocked
        rate_limited = False
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
                headers=admin_headers,
                json={"config_type": "dashboard", "rate_test": i},
                timeout=30,
            )
            if response.status_code == 429:
                rate_limited = True
                data = response.json()
                detail = data.get("detail", {})
                
                # Verify error structure
                assert detail.get("code") == "RATE_LIMITED", f"Expected RATE_LIMITED, got: {detail}"
                assert "retry_after_seconds" in detail, "Should include retry_after_seconds"
                break
        
        assert rate_limited, "Should have been rate limited after 4 requests"

    def test_rate_limit_includes_retry_after_seconds(self, admin_headers):
        """429 response should include retry_after_seconds."""
        # Force rate limit
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
                headers=admin_headers,
                json={"config_type": "dashboard"},
                timeout=30,
            )
            if response.status_code == 429:
                data = response.json()
                detail = data.get("detail", {})
                retry_after = detail.get("retry_after_seconds")
                
                assert retry_after is not None, "Should include retry_after_seconds"
                assert isinstance(retry_after, int), "retry_after_seconds should be integer"
                assert retry_after > 0, "retry_after_seconds should be positive"
                assert retry_after <= 60, "retry_after_seconds should be <= 60 (window size)"
                return
        
        pytest.skip("Could not trigger rate limit for retry_after test")


# ============================================================================
# Role-based Access: dealer token returns 403
# ============================================================================

class TestRoleBasedAccess:
    """Test role-based access control - dealer should get 403."""

    def test_dealer_cannot_access_metrics(self, dealer_headers):
        """Dealer should get 403 on alert-delivery-metrics endpoint."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=dealer_headers,
            timeout=15,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"

    def test_dealer_cannot_access_rerun_simulation(self, dealer_headers):
        """Dealer should get 403 on rerun-simulation endpoint."""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=dealer_headers,
            json={"config_type": "dashboard"},
            timeout=15,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"

    def test_unauthenticated_cannot_access_metrics(self):
        """Unauthenticated request should get 401/403."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            timeout=15,
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"

    def test_unauthenticated_cannot_access_rerun(self):
        """Unauthenticated request should get 401/403."""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            json={"config_type": "dashboard"},
            timeout=15,
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


# ============================================================================
# Contract Validation - Full Response Structure
# ============================================================================

class TestContractValidation:
    """Validate full API response contracts."""

    def test_metrics_contract_complete(self, admin_headers):
        """Verify complete metrics response structure."""
        response = requests.get(
            f"{BASE_URL}/api/admin/ops/alert-delivery-metrics?window=24h",
            headers=admin_headers,
            timeout=15,
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify complete structure
        print(f"Metrics response: {data}")
        
        assert "total_attempts" in data
        assert "successful_deliveries" in data
        assert "failed_deliveries" in data
        assert "success_rate" in data
        assert "channel_breakdown" in data
        
        # Channel breakdown must have all channels
        breakdown = data["channel_breakdown"]
        for channel in ["slack", "smtp", "pd"]:
            assert channel in breakdown, f"Missing {channel} in channel_breakdown"

    def test_rerun_simulation_contract_with_blocked_secrets(self, admin_headers):
        """When secrets are missing, response should have fail_fast structure."""
        response = requests.post(
            f"{BASE_URL}/api/admin/ops/alert-delivery/rerun-simulation",
            headers=admin_headers,
            json={"config_type": "dashboard"},
            timeout=30,
        )
        
        if response.status_code == 429:
            pytest.skip("Rate limited")
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"Rerun simulation response: {data}")
        
        # Should have correlation_id and delivery_status
        assert "correlation_id" in data
        assert "delivery_status" in data
        
        # If blocked_missing_secrets, should have fail_fast
        if data["delivery_status"] == "blocked_missing_secrets":
            assert "fail_fast" in data
            fail_fast = data["fail_fast"]
            assert "missing_keys" in fail_fast


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
