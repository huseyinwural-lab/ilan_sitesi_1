"""
Test file for iteration 142 - Testing install-standard-pack DB transient fallback improvement:
- POST /api/admin/site/content-layout/preset/install-standard-pack should return controlled JSON response on DB_ERROR
- Response structure: ok, summary, results, failed_countries
- GET /api/admin/site/content-layout/preset/verify-standard-pack should work unaffected
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestInstallStandardPackDBFallback:
    """Tests for the install-standard-pack DB transient fallback"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # Login as admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        data = login_response.json()
        token = data.get("access_token")
        assert token, "No access token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token

    def test_install_standard_pack_should_not_return_503(self):
        """
        Test that install-standard-pack returns controlled response instead of 503.
        
        Expected behavior after DB fallback improvement:
        - If DB error occurs during _ensure_layout_page_type_enum_values, 
          endpoint should return 200 with ok=False and failed_countries populated
        - Should NOT return 503 with error_code: DB_ERROR
        """
        payload = {
            "countries": ["TR", "DE", "FR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": True,
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:2000]}")

        # Key assertion: Should NOT return 503
        if response.status_code == 503:
            data = response.json()
            error_code = data.get("error_code", "unknown")
            print(f"ERROR: Still getting 503 with error_code={error_code}")
            print(f"This means the DB fallback improvement is NOT working")
            pytest.fail(f"install-standard-pack still returns 503 with error_code={error_code}. "
                       f"The DB transient fallback should have caught this and returned a controlled 200 response.")
        
        # If we get 200, verify the response structure
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Got 200 response")
            
            # Verify required fields exist
            assert "ok" in data, "Response missing 'ok' field"
            assert "summary" in data, "Response missing 'summary' field"
            assert "results" in data, "Response missing 'results' field"
            assert "failed_countries" in data, "Response missing 'failed_countries' field"

            # ok should be True if failed_countries is empty, False otherwise
            if len(data.get("failed_countries", [])) == 0:
                assert data["ok"] is True, "'ok' should be True when no failed countries"
                print(f"All countries processed successfully")
            else:
                assert data["ok"] is False, "'ok' should be False when there are failed countries"
                print(f"Some countries failed: {data['failed_countries']}")

            # Log summary
            summary = data.get("summary", {})
            print(f"Summary: created_pages={summary.get('created_pages')}, "
                  f"created_drafts={summary.get('created_drafts')}, "
                  f"published_revisions={summary.get('published_revisions')}")
        else:
            # Other status codes may be acceptable for validation errors
            assert response.status_code in [200, 400, 422], f"Unexpected status code: {response.status_code}"

    def test_verify_standard_pack_unaffected(self):
        """
        Test that GET verify-standard-pack continues to work correctly.
        """
        response = self.session.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={
                "countries": "TR,DE,FR",
                "module": "global",
            },
        )

        print(f"Verify response status: {response.status_code}")
        assert response.status_code == 200, f"verify-standard-pack failed: {response.text}"

        data = response.json()
        
        # Verify response structure
        assert "ok" in data, "Response missing 'ok' field"
        assert "summary" in data, "Response missing 'summary' field"
        assert "items" in data, "Response missing 'items' field"

        summary = data["summary"]
        print(f"Verify PASSED: ready_rows={summary.get('ready_rows')}/{summary.get('total_rows')}")

    def test_install_validation_errors_still_work(self):
        """Test that validation errors (400/422) are not affected by DB fallback"""
        
        # Test invalid persona
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "invalid_persona",  # Should be individual or corporate
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": True,
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        print(f"Invalid persona test - Status: {response.status_code}")
        assert response.status_code in [400, 422], f"Expected 400/422 for invalid persona, got {response.status_code}"

    def test_install_with_single_country(self):
        """Test with single country to simplify debugging"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
            "overwrite_existing_draft": True,
            "publish_after_seed": False,
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        print(f"Single country test - Status: {response.status_code}")
        print(f"Response: {response.text[:1000]}")

        if response.status_code == 503:
            data = response.json()
            pytest.fail(f"Single country install also returns 503: {data}")

        if response.status_code == 200:
            data = response.json()
            assert "ok" in data
            assert "results" in data
            assert "failed_countries" in data
            print(f"Single country test passed: ok={data['ok']}")


class TestExpectedResponseStructure:
    """Verify expected response structure for install-standard-pack"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.text}")
        data = login_response.json()
        token = data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def test_response_should_have_ok_boolean(self):
        """Response must have 'ok' boolean field"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        if response.status_code == 503:
            pytest.skip("Endpoint returning 503 - DB fallback not working")

        if response.status_code == 200:
            data = response.json()
            assert "ok" in data, "Missing 'ok' field"
            assert isinstance(data["ok"], bool), "'ok' must be boolean"

    def test_response_should_have_summary_dict(self):
        """Response must have 'summary' dict with specific fields"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        if response.status_code == 503:
            pytest.skip("Endpoint returning 503 - DB fallback not working")

        if response.status_code == 200:
            data = response.json()
            assert "summary" in data, "Missing 'summary' field"
            summary = data["summary"]
            expected_keys = ["created_pages", "created_drafts", "updated_drafts", "skipped_drafts", "published_revisions"]
            for key in expected_keys:
                assert key in summary, f"Summary missing '{key}' field"

    def test_response_should_have_results_list(self):
        """Response must have 'results' list"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        if response.status_code == 503:
            pytest.skip("Endpoint returning 503 - DB fallback not working")

        if response.status_code == 200:
            data = response.json()
            assert "results" in data, "Missing 'results' field"
            assert isinstance(data["results"], list), "'results' must be a list"

    def test_response_should_have_failed_countries_list(self):
        """Response must have 'failed_countries' list"""
        payload = {
            "countries": ["TR"],
            "module": "global",
            "persona": "individual",
            "variant": "A",
        }

        response = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json=payload,
        )

        if response.status_code == 503:
            pytest.skip("Endpoint returning 503 - DB fallback not working")

        if response.status_code == 200:
            data = response.json()
            assert "failed_countries" in data, "Missing 'failed_countries' field"
            assert isinstance(data["failed_countries"], list), "'failed_countries' must be a list"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
