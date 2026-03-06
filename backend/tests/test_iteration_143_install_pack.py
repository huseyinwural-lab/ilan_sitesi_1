"""
Test: install-standard-pack endpoint returns controlled JSON response (200) 
even when DB issues occur, with failed_countries field populated.
Previous iterations 140-142 reported 503 DB_ERROR instead of controlled response.

Iteration 143: Testing the fix that wraps DB operations to avoid re-raising.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin and return token"""
    login_url = f"{BASE_URL}/api/auth/login"
    payload = {"email": "admin@platform.com", "password": "Admin123!"}
    response = requests.post(login_url, json=payload)
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    data = response.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        pytest.skip(f"No token in login response: {data}")
    return token


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


class TestInstallStandardPackDBFallback:
    """Test that install-standard-pack returns controlled JSON response with failed_countries"""

    def test_install_standard_pack_basic_call(self, auth_headers):
        """
        Test POST /api/admin/site/content-layout/preset/install-standard-pack
        This is the main test to verify the endpoint returns a JSON response
        with status 200 and proper structure (ok, summary, results, failed_countries)
        """
        url = f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack"
        payload = {
            "countries": ["TR", "DE", "FR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": True
        }
        
        response = requests.post(url, json=payload, headers=auth_headers, timeout=60)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:2000] if response.text else 'empty'}")
        
        # CRITICAL: Must NOT be 503 anymore - should be 200
        assert response.status_code != 503, f"Endpoint still returns 503. Got: {response.text[:500]}"
        
        # Expected: 200 with JSON body
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"
        
        data = response.json()
        
        # Validate response structure
        assert "ok" in data, "Response missing 'ok' field"
        assert "summary" in data, "Response missing 'summary' field"
        assert "results" in data, "Response missing 'results' field"
        assert "failed_countries" in data, "Response missing 'failed_countries' field"
        
        # summary should have expected keys
        summary = data.get("summary", {})
        assert "created_pages" in summary, "summary missing 'created_pages'"
        assert "created_drafts" in summary, "summary missing 'created_drafts'"
        assert "published_revisions" in summary, "summary missing 'published_revisions'"
        
        print(f"ok={data.get('ok')}, failed_countries={data.get('failed_countries')}")
        print(f"summary={summary}")

    def test_install_standard_pack_response_on_success(self, auth_headers):
        """
        Test that successful seeding returns ok=True and empty failed_countries
        """
        url = f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack"
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": False  # Don't publish to keep test fast
        }
        
        response = requests.post(url, json=payload, headers=auth_headers, timeout=60)
        
        print(f"Status: {response.status_code}")
        
        # Must return 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"
        
        data = response.json()
        
        # If DB is healthy and operation succeeds, ok should be True
        if data.get("ok") is True:
            assert data.get("failed_countries") == [], "If ok=True, failed_countries should be empty"
            print(f"SUCCESS: ok=True, created_pages={data['summary'].get('created_pages')}")
        else:
            # If ok=False, there should be failed_countries
            assert len(data.get("failed_countries", [])) > 0, "If ok=False, failed_countries should not be empty"
            print(f"PARTIAL: ok=False, failed_countries={data.get('failed_countries')}")


class TestVerifyStandardPack:
    """Test verify-standard-pack endpoint (should still work)"""

    def test_verify_standard_pack(self, auth_headers):
        """
        GET /api/admin/site/content-layout/preset/verify-standard-pack
        """
        url = f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack"
        params = {"countries": "TR,DE,FR", "module": "global"}
        
        response = requests.get(url, params=params, headers=auth_headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:1000] if response.text else 'empty'}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:500]}"
        
        data = response.json()
        
        # Validate structure
        assert "ok" in data, "Response missing 'ok' field"
        assert "summary" in data, "Response missing 'summary' field"
        assert "items" in data, "Response missing 'items' field"
        
        summary = data.get("summary", {})
        print(f"verify ok={data.get('ok')}, ready_rows={summary.get('ready_rows')}, total_rows={summary.get('total_rows')}")


class TestInstallPackValidation:
    """Test input validation still works"""

    def test_invalid_persona_returns_400(self, auth_headers):
        """Invalid persona should return 400 not 503"""
        url = f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack"
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "invalid_persona",
            "variant": "A"
        }
        
        response = requests.post(url, json=payload, headers=auth_headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        # Should be 400 for invalid input, not 503
        assert response.status_code == 400, f"Expected 400 for invalid persona, got {response.status_code}"

    def test_invalid_variant_returns_400(self, auth_headers):
        """Invalid variant should return 400"""
        url = f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack"
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "X"  # Invalid - must be A or B
        }
        
        response = requests.post(url, json=payload, headers=auth_headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        assert response.status_code == 400, f"Expected 400 for invalid variant, got {response.status_code}"

    def test_empty_countries_returns_422(self, auth_headers):
        """Empty countries array should return validation error"""
        url = f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack"
        payload = {
            "countries": [],  # Empty
            "module": "global"
        }
        
        response = requests.post(url, json=payload, headers=auth_headers, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        # Should be 400 or 422 for validation, not 503
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
