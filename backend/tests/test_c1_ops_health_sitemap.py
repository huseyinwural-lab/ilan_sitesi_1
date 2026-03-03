"""
C-1 Ops + Health + Sitemap Modular Delegation Tests
====================================================

Tests for verifying:
1. Health endpoints: /api/health, /api/health/db, /api/health/migrations
2. Sitemap endpoint: /api/sitemap.xml, /api/sitemaps/{section}.xml
3. Ops endpoints: /api/admin/system/health-summary, /api/admin/system/health-detail
4. Permission-flag + audit regression smoke
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
SUPER_ADMIN_CREDS = {"email": "admin@platform.com", "password": "Admin123!"}
COUNTRY_ADMIN_CREDS = {"email": "countryadmin@platform.com", "password": "Country123!"}


@pytest.fixture(scope="module")
def api_client():
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def super_admin_token(api_client):
    """Login as super_admin and return token"""
    resp = api_client.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN_CREDS)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip("Super admin login failed")


@pytest.fixture(scope="module")
def country_admin_token(api_client):
    """Login as country_admin and return token"""
    resp = api_client.post(f"{BASE_URL}/api/auth/login", json=COUNTRY_ADMIN_CREDS)
    if resp.status_code == 200:
        return resp.json().get("access_token")
    pytest.skip("Country admin login failed")


class TestHealthEndpoints:
    """Health endpoints via modular delegation (health_routes.py)"""

    def test_health_check_basic(self, api_client):
        """GET /api/health - public, returns status"""
        resp = api_client.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "status" in data
        print(f"Health check: {data.get('status')}")

    def test_health_db(self, api_client):
        """GET /api/health/db - DB connectivity check"""
        resp = api_client.get(f"{BASE_URL}/api/health/db")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "status" in data
        print(f"Health DB: {data.get('status')}, db_ok: {data.get('db_ok')}")

    def test_health_migrations(self, api_client):
        """GET /api/health/migrations - migration state"""
        resp = api_client.get(f"{BASE_URL}/api/health/migrations")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "status" in data
        print(f"Health migrations: {data.get('status')}")


class TestSitemapEndpoints:
    """Sitemap endpoints via modular delegation (sitemap_routes.py)"""

    def test_sitemap_index(self, api_client):
        """GET /api/sitemap.xml - sitemap index"""
        resp = api_client.get(f"{BASE_URL}/api/sitemap.xml")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        content_type = resp.headers.get("content-type", "")
        assert "xml" in content_type.lower() or "text" in content_type.lower(), f"Expected XML content-type, got {content_type}"
        assert "<?xml" in resp.text or "<sitemapindex" in resp.text or "<urlset" in resp.text, "Expected XML sitemap content"
        print(f"Sitemap index returned, content-type: {content_type}")

    def test_sitemap_section_invalid(self, api_client):
        """GET /api/sitemaps/invalid.xml - non-existent section should return 404 or empty"""
        resp = api_client.get(f"{BASE_URL}/api/sitemaps/invalid.xml")
        # Either 404 or 200 with empty sitemap is acceptable
        assert resp.status_code in (200, 404), f"Expected 200 or 404, got {resp.status_code}: {resp.text}"
        print(f"Sitemap section 'invalid': status={resp.status_code}")


class TestOpsEndpoints:
    """Ops admin endpoints via modular delegation (ops_routes.py)"""

    def test_ops_health_summary_unauthorized(self, api_client):
        """GET /api/admin/system/health-summary - requires auth"""
        resp = api_client.get(f"{BASE_URL}/api/admin/system/health-summary")
        assert resp.status_code in (401, 403), f"Expected 401/403 for unauthenticated, got {resp.status_code}"
        print("Ops health-summary correctly requires auth")

    def test_ops_health_summary_super_admin(self, api_client, super_admin_token):
        """GET /api/admin/system/health-summary - super_admin access"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/admin/system/health-summary", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # Response has db_status, payments_runtime etc
        assert "db_status" in data or "status" in data, f"Expected health summary data, got: {data}"
        print(f"Ops health-summary (super_admin): db_status={data.get('db_status')}")

    def test_ops_health_summary_country_admin(self, api_client, country_admin_token):
        """GET /api/admin/system/health-summary - country_admin access"""
        headers = {"Authorization": f"Bearer {country_admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/admin/system/health-summary", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("Ops health-summary (country_admin): OK")

    def test_ops_health_detail_unauthorized(self, api_client):
        """GET /api/admin/system/health-detail - requires auth"""
        resp = api_client.get(f"{BASE_URL}/api/admin/system/health-detail")
        assert resp.status_code in (401, 403), f"Expected 401/403 for unauthenticated, got {resp.status_code}"
        print("Ops health-detail correctly requires auth")

    def test_ops_health_detail_super_admin(self, api_client, super_admin_token):
        """GET /api/admin/system/health-detail - super_admin access"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/admin/system/health-detail", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Ops health-detail (super_admin): keys={list(data.keys()) if isinstance(data, dict) else 'not-dict'}")


class TestPermissionFlagRegression:
    """Smoke test: permission-flag endpoints still working"""

    def test_permissions_me_super_admin(self, api_client, super_admin_token):
        """GET /api/admin/permissions/me - super_admin should get full permissions"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/admin/permissions/me", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        print(f"Permission /me (super_admin): domains={list(data.keys())}")

    def test_permissions_me_country_admin(self, api_client, country_admin_token):
        """GET /api/admin/permissions/me - country_admin"""
        headers = {"Authorization": f"Bearer {country_admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/admin/permissions/me", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        print(f"Permission /me (country_admin): domains={list(data.keys())}")


class TestAuditRegression:
    """Smoke test: audit log endpoints still working"""

    def test_audit_log_list(self, api_client, super_admin_token):
        """GET /api/admin/audit-logs - audit log access"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        resp = api_client.get(f"{BASE_URL}/api/admin/audit-logs?limit=5", headers=headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data or "logs" in data or isinstance(data, list), f"Expected audit logs, got: {type(data)}"
        items = data.get("items", data.get("logs", data))
        print(f"Audit log list: returned {len(items) if isinstance(items, list) else 'N/A'} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
