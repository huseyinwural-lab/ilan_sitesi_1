"""
Test iteration 140: verify install-standard-pack retry mechanism for 503 transient DB errors
and verify-standard-pack summary response.

Test payload: countries TR,DE,FR, module global, persona individual, variant A
"""
import os
import pytest
import requests
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
AUTH_EMAIL = "admin@platform.com"
AUTH_PASSWORD = "Admin123!"

class TestInstallStandardPackRetry:
    """Test install-standard-pack endpoint with retry mechanism"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token for all tests"""
        # Get auth token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
            timeout=30
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code} - {login_response.text}")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def test_verify_standard_pack_returns_summary(self):
        """
        GET /api/admin/site/content-layout/preset/verify-standard-pack
        Test that endpoint returns summary with ready_rows, total_rows, ready_ratio
        """
        params = {
            "countries": "TR,DE,FR",
            "module": "global"
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params=params,
            headers=self.headers,
            timeout=30
        )
        
        print(f"verify-standard-pack response status: {response.status_code}")
        print(f"verify-standard-pack response: {response.text[:500] if response.text else 'empty'}")
        
        # Status code check
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data validation
        data = response.json()
        assert data.get("ok") == True, "Response should have ok=true"
        assert "summary" in data, "Response should contain 'summary'"
        
        summary = data["summary"]
        assert "ready_rows" in summary, "Summary should contain 'ready_rows'"
        assert "total_rows" in summary, "Summary should contain 'total_rows'"
        assert "ready_ratio" in summary, "Summary should contain 'ready_ratio'"
        
        # Total rows should be 3 countries * 15 page types = 45
        assert summary["total_rows"] == 45, f"Expected 45 total_rows (3 countries * 15 page types), got {summary['total_rows']}"
        
        print(f"verify-standard-pack SUCCESS: ready_rows={summary['ready_rows']}, total_rows={summary['total_rows']}, ready_ratio={summary['ready_ratio']}%")
    
    def test_install_standard_pack_success_with_retry(self):
        """
        POST /api/admin/site/content-layout/preset/install-standard-pack
        Test that endpoint succeeds with retry mechanism for transient DB errors
        """
        payload = {
            "countries": ["TR", "DE", "FR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": True
        }
        
        # Attempt installation with retry logic
        max_attempts = 3
        last_response = None
        
        for attempt in range(max_attempts):
            print(f"install-standard-pack attempt {attempt + 1}/{max_attempts}")
            
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
                json=payload,
                headers=self.headers,
                timeout=120  # Longer timeout for DB operations
            )
            
            last_response = response
            print(f"Attempt {attempt + 1} status: {response.status_code}")
            
            if response.status_code == 200:
                print("install-standard-pack SUCCESS on attempt", attempt + 1)
                break
            elif response.status_code == 503:
                print(f"Got 503, will retry (transient DB error expected to be handled by internal retry)")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before external retry
            else:
                print(f"Got non-503 error: {response.text}")
                break
        
        print(f"install-standard-pack final response: {last_response.text[:1000] if last_response.text else 'empty'}")
        
        # Assert success - the retry mechanism should handle transient 503s
        assert last_response.status_code == 200, f"Expected 200 after retries, got {last_response.status_code}: {last_response.text[:500]}"
        
        # Validate response structure
        data = last_response.json()
        assert data.get("ok") == True, "Response should have ok=true"
        assert "summary" in data, "Response should contain 'summary'"
        assert "results" in data, "Response should contain 'results'"
        
        summary = data["summary"]
        print(f"install-standard-pack summary: created_pages={summary.get('created_pages')}, published={summary.get('published_revisions')}")
        
        # Validate response fields
        assert data.get("module") == "global", "Module should be 'global'"
        assert set(data.get("countries", [])) == {"TR", "DE", "FR"}, "Countries should be TR, DE, FR"
        assert data.get("persona") == "individual", "Persona should be 'individual'"
        assert data.get("variant") == "A", "Variant should be 'A'"
    
    def test_install_then_verify_pack(self):
        """
        Integration test: install then verify the pack
        """
        # First install
        install_payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": True
        }
        
        install_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=install_payload,
            headers=self.headers,
            timeout=120
        )
        
        print(f"Install response status: {install_response.status_code}")
        
        # Then verify
        verify_response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={"countries": "TR", "module": "global"},
            headers=self.headers,
            timeout=30
        )
        
        print(f"Verify response status: {verify_response.status_code}")
        
        assert verify_response.status_code == 200, f"Verify failed: {verify_response.text}"
        
        verify_data = verify_response.json()
        summary = verify_data.get("summary", {})
        
        print(f"After install - verify summary: {summary}")
        
        # If install succeeded, we should have some ready rows
        if install_response.status_code == 200:
            assert summary.get("ready_rows", 0) > 0, "After install, should have ready rows"
            print(f"Integration test SUCCESS: {summary['ready_rows']}/{summary['total_rows']} rows ready ({summary['ready_ratio']}%)")


class TestInstallEndpointValidation:
    """Test install-standard-pack endpoint validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token for all tests"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
            timeout=30
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def test_install_invalid_persona_returns_400(self):
        """Test that invalid persona returns 400"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "invalid_persona",
            "variant": "A"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
            headers=self.headers,
            timeout=30
        )
        
        print(f"Invalid persona test: status={response.status_code}")
        assert response.status_code == 400, f"Expected 400 for invalid persona, got {response.status_code}"
    
    def test_install_invalid_variant_returns_400(self):
        """Test that invalid variant returns 400"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "X"  # Invalid - should be A or B
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
            headers=self.headers,
            timeout=30
        )
        
        print(f"Invalid variant test: status={response.status_code}")
        assert response.status_code == 400, f"Expected 400 for invalid variant, got {response.status_code}"
    
    def test_install_empty_countries_returns_400(self):
        """Test that empty countries returns 400"""
        payload = {
            "countries": [],
            "module": "global",
            "persona": "individual",
            "variant": "A"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
            headers=self.headers,
            timeout=30
        )
        
        print(f"Empty countries test: status={response.status_code}")
        assert response.status_code == 422 or response.status_code == 400, f"Expected 400/422 for empty countries, got {response.status_code}"


class TestVerifyEndpointValidation:
    """Test verify-standard-pack endpoint validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token for all tests"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
            timeout=30
        )
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("token") or data.get("access_token")
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
    
    def test_verify_requires_auth(self):
        """Test that verify endpoint requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={"countries": "TR", "module": "global"},
            timeout=30
        )
        
        print(f"Verify without auth: status={response.status_code}")
        assert response.status_code == 401 or response.status_code == 403, f"Expected 401/403 without auth, got {response.status_code}"
    
    def test_verify_missing_countries_returns_422(self):
        """Test that missing countries query param returns 422"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={"module": "global"},  # Missing countries
            headers=self.headers,
            timeout=30
        )
        
        print(f"Verify missing countries: status={response.status_code}")
        assert response.status_code == 422, f"Expected 422 for missing countries, got {response.status_code}"
    
    def test_verify_missing_module_returns_422(self):
        """Test that missing module query param returns 422"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={"countries": "TR"},  # Missing module
            headers=self.headers,
            timeout=30
        )
        
        print(f"Verify missing module: status={response.status_code}")
        assert response.status_code == 422, f"Expected 422 for missing module, got {response.status_code}"
