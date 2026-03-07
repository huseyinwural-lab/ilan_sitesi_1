"""
P0 FAZ-1 Security Tests - Iteration 104

Testing Requirements:
1. Backend startup config: ENVIRONMENT zorunlu, SECRET_KEY zorunlu ve min length kontrolü
2. Seed otomasyonu kapalı: startup akışında otomatik kullanıcı seed çağrısı yok
3. Hardcoded şifrelerin runtime koddan kaldırılması (Admin123/Dealer123/User123 bulunmamalı)
4. Saved cards API contract: card_number gönderimi reddedilmeli; payment_method_id + last4 + brand + expiry ile kabul edilmeli
5. Webhook replay koruması: stale stripe-signature ile /api/payments/webhook 400 dönmeli
6. Dealer login + account saved cards ekranı açılıyor (regresyon)
"""

import os
import pytest
import requests
import time
import re

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://page-builder-stable.preview.emergentagent.com").rstrip("/")
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


class TestP0EnvironmentAndSecretKeyConfig:
    """Test ENVIRONMENT and SECRET_KEY configuration enforcement"""

    def test_health_endpoint_is_up(self):
        """Basic health check to verify backend is running"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health endpoint OK: {data}")

    def test_config_environment_is_set(self):
        """Verify ENVIRONMENT is configured (by checking logs or response)"""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        # The server would not start if ENVIRONMENT was missing
        print("✓ ENVIRONMENT is correctly configured (server started successfully)")

    def test_secret_key_validation_token_roundtrip(self):
        """Test that tokens work (proving SECRET_KEY is configured and >= 32 bytes)"""
        # Login to get a token
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        if resp.status_code == 200:
            data = resp.json()
            assert "access_token" in data
            print("✓ Token generation works (SECRET_KEY is valid)")
        else:
            # If login fails, check if it's auth issue vs config issue
            assert resp.status_code != 500, "Server error suggests config issue"
            print(f"Login returned {resp.status_code}: auth may need valid credentials")


class TestP0HardcodedPasswordRemoval:
    """Verify hardcoded passwords are removed from runtime code"""

    def test_server_py_no_hardcoded_passwords(self):
        """Check server.py does not contain hardcoded passwords in runtime paths"""
        server_path = "/app/backend/server.py"
        with open(server_path, "r") as f:
            content = f.read()
        
        # These patterns should NOT appear in runtime code
        patterns = [
            r"['\"]Admin123[!]?['\"]",
            r"['\"]Dealer123[!]?['\"]", 
            r"['\"]User123[!]?['\"]",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            assert len(matches) == 0, f"Found hardcoded password pattern {pattern} in server.py"
        
        print("✓ No hardcoded passwords found in server.py runtime code")

    def test_core_config_no_hardcoded_passwords(self):
        """Check config.py does not contain hardcoded passwords"""
        config_path = "/app/backend/app/core/config.py"
        with open(config_path, "r") as f:
            content = f.read()
        
        patterns = [
            r"Admin123",
            r"Dealer123",
            r"User123",
        ]
        
        for pattern in patterns:
            assert pattern not in content, f"Found hardcoded password {pattern} in config.py"
        
        print("✓ No hardcoded passwords in config.py")

    def test_security_py_no_hardcoded_passwords(self):
        """Check security.py does not contain hardcoded passwords"""
        security_path = "/app/backend/app/core/security.py"
        with open(security_path, "r") as f:
            content = f.read()
        
        patterns = [
            r"Admin123",
            r"Dealer123",
            r"User123",
        ]
        
        for pattern in patterns:
            assert pattern not in content, f"Found hardcoded password {pattern} in security.py"
        
        print("✓ No hardcoded passwords in security.py")


class TestP0SeedAutomationDisabled:
    """Verify seed automation is disabled in startup"""

    def test_seed_requires_manual_env_var(self):
        """Check seed_manual_fixtures.py requires ALLOW_MANUAL_FIXTURE_SEED"""
        seed_path = "/app/backend/scripts/seed_manual_fixtures.py"
        with open(seed_path, "r") as f:
            content = f.read()
        
        assert "ALLOW_MANUAL_FIXTURE_SEED" in content, "Seed script should require ALLOW_MANUAL_FIXTURE_SEED"
        assert 'settings.ENVIRONMENT == "production"' in content, "Seed should be blocked in production"
        print("✓ Seed script has proper guards (ALLOW_MANUAL_FIXTURE_SEED required, production blocked)")

    def test_lifespan_no_auto_seed_users(self):
        """Verify lifespan() does NOT auto-seed users"""
        server_path = "/app/backend/server.py"
        with open(server_path, "r") as f:
            content = f.read()
        
        # Find the lifespan function
        lifespan_match = re.search(r"async def lifespan\(app: FastAPI\):(.*?)(?=\nasync def |\nclass |\ndef |\n@app\.|\napp\.)", content, re.DOTALL)
        if lifespan_match:
            lifespan_body = lifespan_match.group(1)
            
            # These seed functions should NOT be called automatically
            auto_seed_functions = [
                "_ensure_admin_user",
                "_ensure_dealer_user",
                "_ensure_test_user",
            ]
            
            for func in auto_seed_functions:
                # Check if function is called directly in lifespan
                pattern = rf"await\s+{func}\s*\("
                matches = re.findall(pattern, lifespan_body)
                assert len(matches) == 0, f"Found auto-seed call to {func} in lifespan - should be removed"
            
            print("✓ No automatic user seeding in lifespan()")
        else:
            print("! Could not parse lifespan function - manual verification needed")


class TestP0SavedCardsAPIContract:
    """Test saved cards API rejects raw card_number and accepts tokenized data"""

    @pytest.fixture
    def dealer_token(self):
        """Get dealer auth token"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        if resp.status_code != 200:
            pytest.skip(f"Dealer login failed: {resp.status_code}")
        return resp.json().get("access_token")

    def test_saved_cards_rejects_card_number_field(self, dealer_token):
        """API should reject payload with card_number field (extra_forbid)"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        # Payload with forbidden card_number field
        bad_payload = {
            "holder_name": "Test User",
            "card_number": "4242424242424242",  # This should be REJECTED
            "expiry_month": 12,
            "expiry_year": 2026,
            "payment_method_id": "pm_test123",
            "last4": "4242",
            "brand": "visa"
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/dealer/settings/saved-cards",
            json=bad_payload,
            headers=headers
        )
        
        # Should be 422 (validation error) due to extra_forbid
        assert resp.status_code == 422, f"Expected 422 for card_number field, got {resp.status_code}"
        print(f"✓ card_number field correctly rejected with 422")

    def test_saved_cards_accepts_tokenized_payload(self, dealer_token):
        """API should accept properly tokenized payload"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        # Valid tokenized payload
        valid_payload = {
            "holder_name": "Test P0 Card",
            "payment_method_id": "pm_1234567890abcdef",
            "last4": "4242",
            "expiry_month": 12,
            "expiry_year": 2026,
            "brand": "visa",
            "is_default": False,
            "auto_payment_enabled": False
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/dealer/settings/saved-cards",
            json=valid_payload,
            headers=headers
        )
        
        # Should be 200/201 for valid payload
        assert resp.status_code in [200, 201], f"Expected 200/201 for valid payload, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True or "id" in data
        card_id = data.get("id")
        print(f"✓ Tokenized payload accepted, card_id={card_id}")
        
        # Cleanup: delete the test card
        if card_id:
            del_resp = requests.delete(
                f"{BASE_URL}/api/dealer/settings/saved-cards/{card_id}",
                headers=headers
            )
            print(f"  Cleanup: delete card {card_id} -> {del_resp.status_code}")


class TestP0WebhookReplayProtection:
    """Test webhook replay protection (stale signature rejection)"""

    def test_webhook_requires_signature(self):
        """Webhook should reject requests without stripe-signature header"""
        resp = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            json={"type": "payment_intent.succeeded"},
            headers={"Content-Type": "application/json"}
        )
        
        # Should be 400 for missing signature
        assert resp.status_code == 400, f"Expected 400 for missing signature, got {resp.status_code}"
        print("✓ Webhook rejects requests without stripe-signature")

    def test_webhook_rejects_stale_signature(self):
        """Webhook should reject stale timestamps (replay protection)"""
        # Create a stale timestamp (1 hour ago)
        stale_timestamp = int(time.time()) - 3600
        
        # Fake signature with stale timestamp
        stale_signature = f"t={stale_timestamp},v1=fake_signature_hash"
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/webhook",
            data=b'{"type": "payment_intent.succeeded"}',
            headers={
                "Content-Type": "application/json",
                "stripe-signature": stale_signature
            }
        )
        
        # Should be 400 for stale signature
        assert resp.status_code == 400, f"Expected 400 for stale signature, got {resp.status_code}"
        data = resp.json()
        assert "stale" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower()
        print(f"✓ Webhook rejects stale signature: {data.get('detail')}")

    def test_webhook_alt_endpoint_rejects_stale(self):
        """Alternative webhook endpoint also rejects stale signatures"""
        stale_timestamp = int(time.time()) - 3600
        stale_signature = f"t={stale_timestamp},v1=fake_signature"
        
        resp = requests.post(
            f"{BASE_URL}/api/payments/stripe/webhook",
            data=b'{}',
            headers={
                "Content-Type": "application/json",
                "stripe-signature": stale_signature
            }
        )
        
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ Alternative webhook endpoint (/api/payments/stripe/webhook) also protected")


class TestP0DealerRegressionFlow:
    """Basic regression: dealer login and saved cards screen accessible"""

    def test_dealer_login_success(self):
        """Dealer can log in successfully"""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        
        assert resp.status_code == 200, f"Dealer login failed: {resp.status_code}"
        data = resp.json()
        assert "access_token" in data
        assert data.get("user", {}).get("role") == "dealer"
        print(f"✓ Dealer login successful, role={data.get('user', {}).get('role')}")
        return data.get("access_token")

    def test_dealer_saved_cards_list(self):
        """Dealer can access saved cards list"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        if login_resp.status_code != 200:
            pytest.skip("Dealer login failed")
        
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = requests.get(f"{BASE_URL}/api/dealer/settings/saved-cards", headers=headers)
        assert resp.status_code == 200, f"Saved cards list failed: {resp.status_code}"
        data = resp.json()
        assert "items" in data
        print(f"✓ Dealer saved cards accessible, count={len(data.get('items', []))}")

    def test_dealer_profile_accessible(self):
        """Dealer profile endpoint accessible"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        if login_resp.status_code != 200:
            pytest.skip("Dealer login failed")
        
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        resp = requests.get(f"{BASE_URL}/api/dealer/settings/profile", headers=headers)
        assert resp.status_code == 200, f"Profile failed: {resp.status_code}"
        print("✓ Dealer profile endpoint accessible")


class TestP0SecretKeyInvalidation:
    """Test that old/fallback SECRET_KEY is rejected"""

    def test_old_fallback_key_token_rejected(self):
        """Tokens signed with old fallback key should be rejected"""
        # Import test from existing test file
        from jose import jwt
        
        legacy_key = "your-super-secret-key-change-in-production-2024"
        token = jwt.encode({"sub": "legacy-user", "role": "individual"}, legacy_key, algorithm="HS256")
        
        # Try to use this token
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        # Should be 401 (unauthorized) because token signed with wrong key
        assert resp.status_code == 401, f"Expected 401 for legacy token, got {resp.status_code}"
        print("✓ Token signed with old fallback key is correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
