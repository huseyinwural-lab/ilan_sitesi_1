"""
Audit Dashboard MVP Tests - Iteration 92
Tests for:
- /api/admin/audit/dashboard/schema (RBAC: super_admin only)
- /api/admin/audit/dashboard/events (RBAC: super_admin only)
- /api/admin/audit/dashboard/stats (RBAC: super_admin only)
- /api/admin/audit/dashboard/anomalies (RBAC: super_admin only)

Expected RBAC:
- super_admin: 200
- country_admin: 403
- admin: 403
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from requirements
SUPER_ADMIN = {"email": "admin@platform.com", "password": "Admin123!"}
COUNTRY_ADMIN = {"email": "countryadmin@platform.com", "password": "Country123!"}


def get_token(email: str, password: str) -> str:
    """Login and return access token"""
    # Try login endpoint first
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json().get("access_token", "")
    # Fallback to token endpoint
    resp = requests.post(
        f"{BASE_URL}/api/auth/token",
        json={"email": email, "password": password},
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json().get("access_token", "")
    return ""


@pytest.fixture(scope="module")
def super_admin_token():
    """Get super_admin token"""
    token = get_token(SUPER_ADMIN["email"], SUPER_ADMIN["password"])
    if not token:
        pytest.skip("Failed to get super_admin token")
    return token


@pytest.fixture(scope="module")
def country_admin_token():
    """Get country_admin token"""
    token = get_token(COUNTRY_ADMIN["email"], COUNTRY_ADMIN["password"])
    if not token:
        pytest.skip("Failed to get country_admin token")
    return token


class TestAuditDashboardSchema:
    """Tests for /api/admin/audit/dashboard/schema"""
    
    def test_super_admin_gets_200(self, super_admin_token):
        """super_admin should get 200 for schema endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/schema",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "schema_version" in data
        assert "collection_start_at" in data
        assert "masking_standard" in data
        print(f"PASS: super_admin schema endpoint returned 200 with schema_version={data.get('schema_version')}")
    
    def test_country_admin_gets_403(self, country_admin_token):
        """country_admin should get 403 for schema endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/schema",
            headers={"Authorization": f"Bearer {country_admin_token}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("PASS: country_admin correctly blocked from schema endpoint")


class TestAuditDashboardEvents:
    """Tests for /api/admin/audit/dashboard/events"""
    
    def test_super_admin_gets_200(self, super_admin_token):
        """super_admin should get 200 for events endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/events",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            params={"limit": 10},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "items" in data
        assert "schema_version" in data
        print(f"PASS: super_admin events endpoint returned 200 with {len(data.get('items', []))} items")
    
    def test_country_admin_gets_403(self, country_admin_token):
        """country_admin should get 403 for events endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/events",
            headers={"Authorization": f"Bearer {country_admin_token}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("PASS: country_admin correctly blocked from events endpoint")
    
    def test_events_with_filters(self, super_admin_token):
        """Test events endpoint with filters"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/events",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            params={"action": "login_success", "limit": 5},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "items" in data
        print(f"PASS: events with action filter returned {len(data.get('items', []))} items")


class TestAuditDashboardStats:
    """Tests for /api/admin/audit/dashboard/stats"""
    
    def test_super_admin_gets_200(self, super_admin_token):
        """super_admin should get 200 for stats endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/stats",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "windows" in data
        assert "24h" in data.get("windows", {})
        assert "7d" in data.get("windows", {})
        windows = data.get("windows", {})
        print(f"PASS: super_admin stats endpoint returned 200 with 24h and 7d windows")
        print(f"  24h: total_events={windows.get('24h', {}).get('total_events')}")
        print(f"  7d: total_events={windows.get('7d', {}).get('total_events')}")
    
    def test_country_admin_gets_403(self, country_admin_token):
        """country_admin should get 403 for stats endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/stats",
            headers={"Authorization": f"Bearer {country_admin_token}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("PASS: country_admin correctly blocked from stats endpoint")


class TestAuditDashboardAnomalies:
    """Tests for /api/admin/audit/dashboard/anomalies"""
    
    def test_super_admin_gets_200(self, super_admin_token):
        """super_admin should get 200 for anomalies endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/anomalies",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "anomalies" in data
        assert "thresholds" in data
        anomalies = data.get("anomalies", [])
        print(f"PASS: super_admin anomalies endpoint returned 200 with {len(anomalies)} anomalies")
    
    def test_country_admin_gets_403(self, country_admin_token):
        """country_admin should get 403 for anomalies endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/anomalies",
            headers={"Authorization": f"Bearer {country_admin_token}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("PASS: country_admin correctly blocked from anomalies endpoint")
    
    def test_anomalies_with_custom_thresholds(self, super_admin_token):
        """Test anomalies endpoint with custom thresholds"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/anomalies",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            params={
                "window_hours": 48,
                "deny_403_threshold": 1,
                "publish_failure_threshold": 1,
                "export_attempt_threshold": 1,
            },
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert "anomalies" in data
        print(f"PASS: anomalies with custom thresholds returned {len(data.get('anomalies', []))} anomalies")


class TestAuditDashboardRBACEnforcement:
    """Comprehensive RBAC enforcement tests"""
    
    def test_all_endpoints_require_super_admin(self, country_admin_token):
        """All audit dashboard endpoints should block non-super_admin roles"""
        endpoints = [
            "/api/admin/audit/dashboard/schema",
            "/api/admin/audit/dashboard/events",
            "/api/admin/audit/dashboard/stats",
            "/api/admin/audit/dashboard/anomalies",
        ]
        
        for endpoint in endpoints:
            resp = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {country_admin_token}"},
            )
            assert resp.status_code == 403, f"Expected 403 for {endpoint}, got {resp.status_code}"
            print(f"PASS: {endpoint} correctly returns 403 for country_admin")
    
    def test_unauthenticated_gets_401(self):
        """Unauthenticated requests should get 401"""
        endpoints = [
            "/api/admin/audit/dashboard/schema",
            "/api/admin/audit/dashboard/events",
            "/api/admin/audit/dashboard/stats",
            "/api/admin/audit/dashboard/anomalies",
        ]
        
        for endpoint in endpoints:
            resp = requests.get(f"{BASE_URL}{endpoint}")
            assert resp.status_code in (401, 403), f"Expected 401/403 for {endpoint}, got {resp.status_code}"
            print(f"PASS: {endpoint} correctly blocks unauthenticated requests")
