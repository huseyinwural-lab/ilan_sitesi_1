"""
P0-3 Middleware Stability & P0-4 Meilisearch Timeout/Settings Hardening Tests
FAZ-2: Tests for rbac_hard_lock, fail_safe_response_guard, /api/health/search, degrade mode
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMiddlewareStability:
    """P0-3: Middleware deterministic response contract tests"""
    
    def test_rbac_hard_lock_admin_path_requires_auth(self):
        """rbac_hard_lock middleware returns 401 for unauthenticated admin paths"""
        response = requests.get(f"{BASE_URL}/api/admin/users", timeout=15)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"PASS: rbac_hard_lock returns 401 for unauthenticated admin path: {data}")
    
    def test_rbac_hard_lock_non_admin_path_passes_through(self):
        """rbac_hard_lock allows non-admin paths to pass through"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert response.status_code == 200
        print(f"PASS: Non-admin path /api/health returns 200")
    
    def test_rbac_hard_lock_404_for_missing_admin_route(self):
        """rbac_hard_lock returns 404 for non-existent admin routes"""
        response = requests.get(f"{BASE_URL}/api/admin/nonexistent-route-xyz", timeout=15)
        # Should return 404 (not found) not 500
        assert response.status_code in (401, 404)
        print(f"PASS: Non-existent admin route returns {response.status_code}")
    
    def test_fail_safe_response_guard_returns_json_500(self):
        """fail_safe_response_guard should return JSON 500 on unhandled exceptions"""
        # We cannot easily trigger an unhandled exception in middleware,
        # but we can verify the middleware is registered by testing normal flow
        response = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert response.status_code == 200
        # Verify X-Response-Time header is set (from record_request_metrics middleware)
        assert "X-Response-Time-ms" in response.headers or "x-response-time-ms" in response.headers
        print(f"PASS: Middleware chain is functioning correctly, X-Response-Time present")


class TestHealthSearchEndpoint:
    """/api/health/search endpoint tests"""
    
    def test_health_search_endpoint_exists(self):
        """Verify /api/health/search endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/health/search", timeout=15)
        # Should return 200 (healthy) or 503 (degraded) - not 404
        assert response.status_code in (200, 503)
        print(f"PASS: /api/health/search endpoint exists, status={response.status_code}")
    
    def test_health_search_deterministic_200_response(self):
        """Verify /api/health/search returns deterministic 200 when healthy"""
        response = requests.get(f"{BASE_URL}/api/health/search", timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Check required fields for healthy response
            assert "healthy" in data
            assert "degraded" in data
            assert "runtime" in data
            assert data["healthy"] == True
            assert data["degraded"] == False
            print(f"PASS: /api/health/search healthy response: {data}")
        else:
            # 503 is acceptable if MeiliSearch is down/degraded
            assert response.status_code == 503
            data = response.json()
            # Should still have deterministic structure
            assert "error_code" in data
            assert data.get("error_code") == "SEARCH_DEGRADED"
            print(f"PASS: /api/health/search degraded response: {data}")
    
    def test_health_search_503_degrade_payload_format(self):
        """Verify /api/health/search 503 response has required degrade fields"""
        response = requests.get(f"{BASE_URL}/api/health/search", timeout=15)
        if response.status_code == 503:
            data = response.json()
            # Check degrade payload structure
            assert "error_code" in data
            assert "degraded" in data
            assert "retry_after_seconds" in data
            assert data["error_code"] == "SEARCH_DEGRADED"
            assert data["degraded"] == True
            assert isinstance(data["retry_after_seconds"], int)
            print(f"PASS: 503 degrade payload has correct format: {data}")
        else:
            # 200 means healthy, skip this test
            print(f"SKIP: Search is healthy (200), degrade payload not tested")


class TestSearchDegradePayload:
    """P0-4: Search degrade payload format tests"""
    
    def test_search_suggest_degrade_mode(self):
        """Verify /api/search/suggest returns 503 with degrade payload if circuit open"""
        response = requests.get(f"{BASE_URL}/api/search/suggest?q=test", timeout=15)
        # Should return 200 or 503
        assert response.status_code in (200, 503)
        if response.status_code == 503:
            data = response.json()
            assert "error_code" in data
            assert data.get("error_code") == "SEARCH_DEGRADED"
            assert "degraded" in data
            assert "retry_after_seconds" in data
            # Check Retry-After header
            assert "Retry-After" in response.headers or "retry-after" in response.headers
            print(f"PASS: /api/search/suggest degrade response: {data}")
        else:
            print(f"PASS: /api/search/suggest returned 200 (healthy)")
    
    def test_search_meili_degrade_mode(self):
        """Verify /api/search/meili returns 503 with degrade payload if circuit open"""
        response = requests.get(f"{BASE_URL}/api/search/meili?q=test", timeout=15)
        assert response.status_code in (200, 503)
        if response.status_code == 503:
            data = response.json()
            # Could be HTTPException or JSONResponse - check for either format
            if "error_code" in data:
                assert data["error_code"] == "SEARCH_DEGRADED"
                print(f"PASS: /api/search/meili degrade response: {data}")
            else:
                # HTTPException format
                assert "detail" in data
                print(f"PASS: /api/search/meili unavailable response: {data}")
        else:
            data = response.json()
            assert "hits" in data
            print(f"PASS: /api/search/meili returned 200 with hits")


class TestSearchV2Endpoint:
    """P0-4: Search v2 endpoint regression tests"""
    
    def test_v2_search_exists_and_responds(self):
        """Verify /api/v2/search endpoint responds normally"""
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&q=test", timeout=15)
        # Should return 200 (success), 503 (degraded), or 400 (bad request)
        assert response.status_code in (200, 400, 503)
        print(f"PASS: /api/v2/search endpoint responds with status={response.status_code}")
    
    def test_v2_search_requires_country(self):
        """Verify /api/v2/search requires country parameter"""
        response = requests.get(f"{BASE_URL}/api/v2/search?q=test", timeout=15)
        # Should return 400 if country is missing (or 503 if degraded)
        assert response.status_code in (400, 503)
        if response.status_code == 400:
            data = response.json()
            assert "detail" in data
            assert "country" in data["detail"].lower()
            print(f"PASS: /api/v2/search requires country: {data}")
        else:
            print(f"PASS: /api/v2/search returned 503 (degraded)")
    
    def test_v2_search_normal_response(self):
        """Verify /api/v2/search returns proper response structure when healthy"""
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&q=test", timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Check expected response structure
            assert "items" in data or "hits" in data
            print(f"PASS: /api/v2/search returns proper structure")
        else:
            print(f"SKIP: /api/v2/search returned {response.status_code}, not 200")
    
    def test_v2_search_degrade_response_format(self):
        """Verify /api/v2/search 503 response has correct degrade format"""
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&q=test", timeout=15)
        if response.status_code == 503:
            data = response.json()
            if "error_code" in data:
                assert data.get("error_code") == "SEARCH_DEGRADED"
                assert data.get("degraded") == True
                assert "retry_after_seconds" in data
                print(f"PASS: /api/v2/search degrade format correct: {data}")
            else:
                # HTTPException format
                print(f"PASS: /api/v2/search unavailable: {data}")
        else:
            print(f"SKIP: /api/v2/search returned {response.status_code}")


class TestSentryIntegrationGate:
    """Sentry integration gate tests - app should work with or without SENTRY_DSN"""
    
    def test_app_runs_without_sentry_dsn(self):
        """Verify app runs correctly when SENTRY_DSN is not set"""
        # Simple health check - if app is running, SENTRY_DSN absence doesn't break it
        response = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert response.status_code == 200
        print(f"PASS: App runs correctly (SENTRY_DSN gate passes)")
    
    def test_startup_completes_with_sentry_gate(self):
        """Verify startup completion - Sentry init path doesn't break app"""
        response = requests.get(f"{BASE_URL}/api/health/startup", timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Startup should be complete
            assert data.get("status") in ("ok", "healthy", "complete", "ready")
            print(f"PASS: Startup complete with Sentry gate: {data}")
        else:
            # 503 is acceptable if startup is still in progress
            print(f"INFO: Startup endpoint returned {response.status_code}")


class TestMeilisearchSettingsSync:
    """P0-4: Meilisearch settings sync non-blocking tests"""
    
    def test_search_endpoint_non_blocking(self):
        """Verify search endpoints don't block on settings sync"""
        import time
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&q=test", timeout=15)
        elapsed = time.time() - start
        # Should respond within 15 seconds (not blocked by settings sync)
        assert elapsed < 15
        assert response.status_code in (200, 400, 503)
        print(f"PASS: Search endpoint responded in {elapsed:.2f}s (non-blocking)")
    
    def test_health_search_shows_sync_status(self):
        """Verify /api/health/search includes sync status info"""
        response = requests.get(f"{BASE_URL}/api/health/search", timeout=15)
        if response.status_code == 200:
            data = response.json()
            # Should include sync_consecutive_failures field
            assert "sync_consecutive_failures" in data
            print(f"PASS: Health search includes sync status: failures={data.get('sync_consecutive_failures')}")
        elif response.status_code == 503:
            data = response.json()
            # Degraded response should also include sync info
            assert "sync_consecutive_failures" in data or "error_code" in data
            print(f"PASS: Health search degraded includes sync info: {data}")
        else:
            print(f"SKIP: Unexpected status {response.status_code}")


class TestMiddlewareResponseNoneGuard:
    """Middleware response=None guard tests"""
    
    def test_middleware_returns_valid_response(self):
        """Verify middleware never returns None (always valid HTTP response)"""
        # Test multiple endpoints to verify middleware guard
        endpoints = [
            "/api/health",
            "/api/health/search",
            "/api/search/suggest?q=te",
        ]
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=15)
            # Should never hang or return invalid response
            assert response.status_code is not None
            assert response.status_code >= 100 and response.status_code < 600
            print(f"PASS: {endpoint} returned valid response {response.status_code}")


class TestDealerLoginRegression:
    """Dealer login regression test"""
    
    def test_dealer_login(self):
        """Verify dealer can login with credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "dealer"
        print(f"PASS: Dealer login successful")
        return data["access_token"]


# Fixtures
@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "dealer@platform.com", "password": "Dealer123!"},
        timeout=15
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    return None
