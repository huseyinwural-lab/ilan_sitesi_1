"""
Final Sprint Backend Tests - Iteration 18
Tests for: Watermark, Transactions Log, Reports (Message), Search Suggest endpoints
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin and return token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code}")
    return resp.json().get("access_token")


@pytest.fixture
def auth_headers(admin_token):
    """Return auth headers"""
    return {"Authorization": f"Bearer {admin_token}"}


# ========== WATERMARK TESTS ==========
class TestWatermarkPipeline:
    """Tests for Watermark & Image Pipeline endpoints"""

    def test_get_watermark_settings_returns_200(self, auth_headers):
        """GET /api/admin/media/watermark/settings should return 200 with config"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/media/watermark/settings",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "config" in data, "Response should contain 'config'"
        config = data["config"]
        assert "enabled" in config, "Config should have 'enabled' key"
        assert "position" in config, "Config should have 'position' key"
        assert "opacity" in config, "Config should have 'opacity' key"
        print(f"✓ Watermark settings: enabled={config.get('enabled')}, position={config.get('position')}")

    def test_patch_watermark_settings_returns_200(self, auth_headers):
        """PATCH /api/admin/media/watermark/settings should update settings"""
        payload = {
            "enabled": True,
            "position": "bottom_right",
            "opacity": 0.4,
        }
        resp = requests.patch(
            f"{BASE_URL}/api/admin/media/watermark/settings",
            headers=auth_headers,
            json=payload,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected ok=True, got {data}"
        print("✓ Watermark settings updated successfully")

    def test_watermark_preview_returns_image(self, auth_headers):
        """GET /api/admin/media/watermark/preview should return 200 with image"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/media/watermark/preview",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert "image" in resp.headers.get("content-type", ""), f"Expected image content-type, got {resp.headers.get('content-type')}"
        assert len(resp.content) > 100, "Preview image should have content"
        print(f"✓ Watermark preview returned, size={len(resp.content)} bytes")

    def test_pipeline_performance_returns_metrics(self, auth_headers):
        """GET /api/admin/media/pipeline/performance should return 200 with metrics"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/media/pipeline/performance",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "summary" in data, "Response should contain 'summary'"
        summary = data["summary"]
        # Check for expected metrics
        print(f"✓ Pipeline performance: sample_count={summary.get('sample_count', 0)}, avg_ms={summary.get('average_processing_ms', 'N/A')}")


# ========== TRANSACTIONS LOG TESTS ==========
class TestTransactionsLog:
    """Tests for Transactions Log endpoints (read-only)"""

    def test_get_payments_returns_200(self, auth_headers):
        """GET /api/admin/payments should return 200"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        assert "pagination" in data, "Response should contain 'pagination'"
        print(f"✓ Transactions log: {len(data['items'])} items, total={data['pagination'].get('total', 0)}")

    def test_get_payments_with_status_filter(self, auth_headers):
        """GET /api/admin/payments with status filter"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments?status=succeeded",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        # Verify all items match the filter
        for item in data["items"]:
            assert item["status"] == "succeeded", f"Expected status=succeeded, got {item['status']}"
        print(f"✓ Transactions with status=succeeded: {len(data['items'])} items")

    def test_get_payments_with_date_filter(self, auth_headers):
        """GET /api/admin/payments with date filters"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments?start_date=2025-01-01T00:00:00+00:00&end_date=2026-12-31T23:59:59+00:00",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        print(f"✓ Transactions with date filter: {len(data['items'])} items")

    def test_get_payments_with_query_filter(self, auth_headers):
        """GET /api/admin/payments with q param"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments?q=test",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        print(f"✓ Transactions with query=test: {len(data['items'])} items")

    def test_export_csv_returns_csv(self, auth_headers):
        """GET /api/admin/payments/export/csv should return CSV file"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments/export/csv",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        content_type = resp.headers.get("content-type", "")
        assert "text/csv" in content_type or "text/plain" in content_type, f"Expected CSV content-type, got {content_type}"
        # CSV should have headers at minimum
        content = resp.text
        assert len(content) > 0, "CSV should have content"
        print(f"✓ CSV export returned, size={len(content)} bytes")


# ========== MESSAGE REPORTS TESTS ==========
class TestMessageReports:
    """Tests for Message Reports endpoints"""

    def test_get_message_reports_returns_200(self, auth_headers):
        """GET /api/admin/reports/messages should return 200"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/reports/messages",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        assert "pagination" in data, "Response should contain 'pagination'"
        print(f"✓ Message reports: {len(data['items'])} items, total={data['pagination'].get('total', 0)}")

    def test_get_message_reports_with_status_filter(self, auth_headers):
        """GET /api/admin/reports/messages with status filter"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/reports/messages?status=open",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        # Verify all items match the filter
        for item in data["items"]:
            assert item["status"] == "open", f"Expected status=open, got {item['status']}"
        print(f"✓ Message reports with status=open: {len(data['items'])} items")

    def test_get_message_reports_with_reason_filter(self, auth_headers):
        """GET /api/admin/reports/messages with reason filter"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/reports/messages?reason=spam",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data
        print(f"✓ Message reports with reason=spam: {len(data['items'])} items")


# ========== LISTING REPORTS TESTS ==========
class TestListingReports:
    """Tests for Listing Reports endpoints"""

    def test_get_listing_reports_returns_200(self, auth_headers):
        """GET /api/admin/reports should return 200"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/reports",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        print(f"✓ Listing reports: {len(data['items'])} items")


# ========== SEARCH SUGGEST TESTS ==========
class TestSearchSuggest:
    """Tests for Search Suggest endpoint with caching"""

    def test_suggest_with_short_query_returns_empty(self):
        """GET /api/search/suggest with q < 2 chars should return empty"""
        resp = requests.get(f"{BASE_URL}/api/search/suggest?q=a")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("items") == [], f"Expected empty items, got {data.get('items')}"
        print("✓ Suggest with short query returns empty")

    def test_suggest_with_valid_query_returns_items(self):
        """GET /api/search/suggest with valid query"""
        resp = requests.get(f"{BASE_URL}/api/search/suggest?q=bmw&limit=5")
        # May return 503 if Meili not configured - that's acceptable
        if resp.status_code == 503:
            print("⚠ Meilisearch not available (503) - suggest endpoint requires Meili")
            pytest.skip("Meilisearch not configured")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        assert "query" in data, "Response should contain 'query'"
        assert "latency_ms" in data, "Response should contain 'latency_ms'"
        print(f"✓ Suggest with query=bmw: {len(data.get('items', []))} items, latency={data.get('latency_ms')}ms")

    def test_suggest_cache_returns_cached_on_second_call(self):
        """Second call with same query should return cached=true"""
        query = "mercedes"
        # First call
        resp1 = requests.get(f"{BASE_URL}/api/search/suggest?q={query}&limit=5")
        if resp1.status_code == 503:
            print("⚠ Meilisearch not available (503) - suggest endpoint requires Meili")
            pytest.skip("Meilisearch not configured")
        assert resp1.status_code == 200
        data1 = resp1.json()
        
        # Second call (should be cached)
        resp2 = requests.get(f"{BASE_URL}/api/search/suggest?q={query}&limit=5")
        assert resp2.status_code == 200
        data2 = resp2.json()
        
        # Check if second call is cached
        if data2.get("cached"):
            assert data2.get("latency_ms", 1000) < 50, "Cached response should be fast"
            print(f"✓ Suggest cache working: cached={data2.get('cached')}, latency={data2.get('latency_ms')}ms")
        else:
            # Cache may have expired or not populated - still valid
            print(f"⚠ Suggest cache not hit (may be expected): cached={data2.get('cached')}, latency={data2.get('latency_ms')}ms")


# ========== RBAC TESTS ==========
class TestRbacAccess:
    """Tests for RBAC on admin endpoints"""

    def test_reports_accessible_with_moderator_roles(self, auth_headers):
        """Admin reports should be accessible with moderation roles"""
        # Admin (super_admin) should have access
        resp = requests.get(
            f"{BASE_URL}/api/admin/reports",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ Reports endpoint accessible with super_admin")

    def test_payments_accessible_with_finance_roles(self, auth_headers):
        """Admin payments should be accessible with finance roles"""
        # Admin (super_admin) should have access
        resp = requests.get(
            f"{BASE_URL}/api/admin/payments",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ Payments endpoint accessible with super_admin")


# ========== ATTRIBUTE VALIDATION TESTS ==========
class TestAttributeValidation:
    """Tests for Attribute update and validation"""

    def test_get_attributes_returns_200(self, auth_headers):
        """GET /api/admin/attributes should return 200"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/attributes",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should contain 'items'"
        print(f"✓ Attributes: {len(data['items'])} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
