"""
Meilisearch Admin Config Tests
Tests for /api/admin/system-settings/meilisearch endpoints
- Active config retrieval
- History endpoint
- Create config -> status inactive
- Activation gate (PASS/FAIL handling)
- Revoke endpoint
- Security: key masking, ciphertext not returned
- RBAC: non-super-admin should get 403
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


class MeiliAdminTestContext:
    admin_token = None
    user_token = None
    created_config_id = None


ctx = MeiliAdminTestContext()


@pytest.fixture(scope="module", autouse=True)
def setup_tokens():
    """Login admin and non-admin user for testing"""
    # Admin login
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if resp.status_code == 200:
        ctx.admin_token = resp.json().get("access_token")
    else:
        pytest.skip(f"Admin login failed: {resp.status_code}")

    # Non-admin user login
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
    )
    if resp.status_code == 200:
        ctx.user_token = resp.json().get("access_token")
    else:
        print(f"Non-admin user login failed: {resp.status_code}")

    yield


# --- RBAC TESTS: Non-super-admin should get 403 ---

class TestMeiliRBAC:
    """RBAC tests - non-super_admin should get 403 on meili admin endpoints"""

    def test_non_admin_get_active_config_403(self):
        """Non-admin user should get 403 on GET /api/admin/system-settings/meilisearch"""
        if not ctx.user_token:
            pytest.skip("Non-admin user token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin user got 403 on GET meilisearch active config")

    def test_non_admin_get_history_403(self):
        """Non-admin user should get 403 on GET /api/admin/system-settings/meilisearch/history"""
        if not ctx.user_token:
            pytest.skip("Non-admin user token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/history",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin user got 403 on GET meilisearch history")

    def test_non_admin_create_config_403(self):
        """Non-admin user should get 403 on POST /api/admin/system-settings/meilisearch"""
        if not ctx.user_token:
            pytest.skip("Non-admin user token not available")
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            json={
                "meili_url": "https://fake.meili.test",
                "meili_index_name": "test_index",
                "meili_master_key": "test_key_123",
            },
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin user got 403 on POST meilisearch create config")

    def test_unauthenticated_request_401(self):
        """Unauthenticated request should get 401"""
        resp = requests.get(f"{BASE_URL}/api/admin/system-settings/meilisearch")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print(f"PASS: Unauthenticated request got 401")


# --- ADMIN TESTS: Active config, history, create, activate, revoke ---

class TestMeiliAdminActive:
    """Admin tests for active config endpoint"""

    def test_get_active_config_returns_200(self):
        """GET /api/admin/system-settings/meilisearch should return 200 for super_admin"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "encryption_key_present" in data, "Response should have encryption_key_present"
        assert "active_config" in data, "Response should have active_config"
        assert "default_index_name" in data, "Response should have default_index_name"
        print(f"PASS: GET active config returned 200, encryption_key_present={data.get('encryption_key_present')}")

    def test_active_config_key_masked(self):
        """Active config response should have master_key_masked, not ciphertext"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        active_config = data.get("active_config")
        if active_config:
            assert "master_key_masked" in active_config, "Should have master_key_masked"
            assert active_config["master_key_masked"] == "••••", "master_key_masked should be masked"
            # Ensure ciphertext is NOT in response
            assert "meili_master_key_ciphertext" not in active_config, "ciphertext should not be in response"
            print(f"PASS: Active config key is masked (••••), ciphertext not exposed")
        else:
            print(f"PASS: No active config, key masking cannot be verified yet")


class TestMeiliAdminHistory:
    """Admin tests for history endpoint"""

    def test_get_history_returns_200(self):
        """GET /api/admin/system-settings/meilisearch/history should return 200"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/history",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should have items list"
        assert isinstance(data["items"], list), "items should be a list"
        print(f"PASS: GET history returned 200, items count={len(data['items'])}")

    def test_history_items_key_masked(self):
        """History items should have master_key_masked, not ciphertext"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/history",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", [])
        for item in items:
            assert "master_key_masked" in item, "Each item should have master_key_masked"
            assert item["master_key_masked"] == "••••", "master_key_masked should be masked"
            assert "meili_master_key_ciphertext" not in item, "ciphertext should not be in response"
        print(f"PASS: History items key masked, ciphertext not exposed (checked {len(items)} items)")


class TestMeiliAdminCreateConfig:
    """Admin tests for creating meilisearch config"""

    def test_create_config_returns_201_and_inactive_status(self):
        """POST /api/admin/system-settings/meilisearch should create config with status=inactive"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        payload = {
            "meili_url": "https://test-meili.example.com",
            "meili_index_name": "test_listings",
            "meili_master_key": "test_master_key_secret_12345",
        }
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json=payload,
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, "Response should have ok=True"
        config = data.get("config")
        assert config is not None, "Response should have config object"
        assert config.get("status") == "inactive", f"New config should be inactive, got {config.get('status')}"
        assert config.get("meili_url") == payload["meili_url"], "Config URL should match"
        assert config.get("meili_index_name") == payload["meili_index_name"], "Config index name should match"
        
        # Store config_id for subsequent tests
        ctx.created_config_id = config.get("id")
        
        # Verify key is masked
        assert config.get("master_key_masked") == "••••", "Key should be masked"
        assert "meili_master_key_ciphertext" not in config, "ciphertext should not be in response"
        
        print(f"PASS: Create config returned 201, status=inactive, config_id={ctx.created_config_id}")

    def test_create_config_validation_missing_url(self):
        """Creating config without URL should fail with 400/422"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        payload = {
            "meili_url": "",
            "meili_master_key": "some_key",
        }
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json=payload,
        )
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}: {resp.text}"
        print(f"PASS: Missing URL returns {resp.status_code}")

    def test_create_config_validation_invalid_url_scheme(self):
        """Creating config with invalid URL scheme should fail"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        payload = {
            "meili_url": "ftp://invalid-scheme.com",
            "meili_master_key": "some_key",
        }
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json=payload,
        )
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}: {resp.text}"
        print(f"PASS: Invalid URL scheme returns {resp.status_code}")


class TestMeiliAdminTestGate:
    """Admin tests for test endpoint (activation gate)"""

    def test_test_endpoint_returns_fail_for_unreachable(self):
        """POST /api/admin/system-settings/meilisearch/{config_id}/test should return FAIL for unreachable meili"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        if not ctx.created_config_id:
            pytest.skip("No config created yet")
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{ctx.created_config_id}/test",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        result = data.get("result", {})
        assert result.get("status") == "FAIL", f"Expected FAIL status for unreachable meili, got {result.get('status')}"
        assert result.get("reason_code") in ("connection_error", "timeout", "unauthorized", "runtime_error"), \
            f"reason_code should indicate connection issue, got {result.get('reason_code')}"
        print(f"PASS: Test endpoint returned FAIL with reason_code={result.get('reason_code')}")

    def test_test_invalid_config_id_returns_404(self):
        """Testing non-existent config should return 404"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{fake_uuid}/test",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print(f"PASS: Test non-existent config returns 404")


class TestMeiliAdminActivate:
    """Admin tests for activate endpoint (activation gate)"""

    def test_activate_fails_without_passing_test(self):
        """Activate endpoint should reject if test does not pass (connection_error expected)"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        if not ctx.created_config_id:
            pytest.skip("No config created yet")
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{ctx.created_config_id}/activate",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Activation should fail because meili is unreachable
        assert data.get("ok") is False or data.get("activated") is False, \
            f"Activation should be rejected, got ok={data.get('ok')}, activated={data.get('activated')}"
        result = data.get("result", {})
        assert result.get("status") == "FAIL", f"Expected FAIL status, got {result.get('status')}"
        print(f"PASS: Activate rejected (test FAIL), reason_code={result.get('reason_code')}")

    def test_activate_invalid_config_id_returns_404(self):
        """Activating non-existent config should return 404"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{fake_uuid}/activate",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print(f"PASS: Activate non-existent config returns 404")


class TestMeiliAdminRevoke:
    """Admin tests for revoke endpoint"""

    def test_revoke_config_returns_200(self):
        """POST /api/admin/system-settings/meilisearch/{config_id}/revoke should return 200"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        if not ctx.created_config_id:
            pytest.skip("No config created yet")
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{ctx.created_config_id}/revoke",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, "Revoke should return ok=True"
        config = data.get("config", {})
        assert config.get("status") == "revoked", f"Config status should be revoked, got {config.get('status')}"
        print(f"PASS: Revoke returned 200, config status=revoked")

    def test_revoke_invalid_config_id_returns_404(self):
        """Revoking non-existent config should return 404"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{fake_uuid}/revoke",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print(f"PASS: Revoke non-existent config returns 404")

    def test_revoked_config_cannot_be_tested(self):
        """Testing a revoked config should return 400"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        if not ctx.created_config_id:
            pytest.skip("No config created yet")
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{ctx.created_config_id}/test",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 400, f"Expected 400 for testing revoked config, got {resp.status_code}: {resp.text}"
        print(f"PASS: Testing revoked config returns 400")

    def test_revoked_config_cannot_be_activated(self):
        """Activating a revoked config should return 400"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        if not ctx.created_config_id:
            pytest.skip("No config created yet")
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/system-settings/meilisearch/{ctx.created_config_id}/activate",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={},
        )
        assert resp.status_code == 400, f"Expected 400 for activating revoked config, got {resp.status_code}: {resp.text}"
        print(f"PASS: Activating revoked config returns 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
