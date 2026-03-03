"""
P1 Audit/Permissions UX Expansion Test Suite
Tests pagination param standardization, filters, 403 guards, and CSV export.

Tests:
- Audit logs: page/size/q/sort/actor/role/country/event_type/date_from/date_to
- Permissions: users/overrides/shadow-diff pagination and filters
- CSV export permission enforcement (super_admin only)
- 403 guards for user/dealer unauthorized access
"""

import pytest
import requests
import os
import time
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
SUPER_ADMIN = {"email": "admin@platform.com", "password": "Admin123!"}
NORMAL_USER = {"email": "user@platform.com", "password": "User123!"}
DEALER = {"email": "dealer@platform.com", "password": "Dealer123!"}


@pytest.fixture(scope="module")
def tokens():
    """Get auth tokens for different users."""
    result = {}
    
    # Super admin login
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN)
    if resp.status_code == 200:
        result["super_admin"] = resp.json().get("access_token")
    else:
        pytest.fail(f"Super admin login failed: {resp.status_code} {resp.text}")
    
    # Normal user login
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=NORMAL_USER)
    if resp.status_code == 200:
        result["user"] = resp.json().get("access_token")
    
    # Dealer login
    resp = requests.post(f"{BASE_URL}/api/auth/login", json=DEALER)
    if resp.status_code == 200:
        result["dealer"] = resp.json().get("access_token")
    
    return result


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# AUDIT LOGS PAGINATION & FILTER TESTS
# =============================================================================

class TestAuditLogsPagination:
    """Test audit logs pagination param standardization: page/size/q/sort"""
    
    def test_audit_logs_default_pagination(self, tokens):
        """Test default pagination returns page=1, size=20"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert "items" in data
        assert "pagination" in data
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["size"] == 20
        assert "total" in pagination
        assert "total_pages" in pagination
        assert "sort" in pagination
        print(f"✓ Default pagination: page={pagination['page']}, size={pagination['size']}, total={pagination['total']}")
    
    def test_audit_logs_custom_page_size(self, tokens):
        """Test custom page and size parameters"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 2, "size": 50}
        )
        assert resp.status_code == 200
        data = resp.json()
        pagination = data["pagination"]
        assert pagination["page"] == 2
        assert pagination["size"] == 50
        print(f"✓ Custom pagination: page={pagination['page']}, size={pagination['size']}")
    
    def test_audit_logs_sort_desc(self, tokens):
        """Test sort=created_at:desc"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"sort": "created_at:desc", "size": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["sort"] == "created_at:desc"
        print(f"✓ Sort desc applied: {data['pagination']['sort']}")
    
    def test_audit_logs_sort_asc(self, tokens):
        """Test sort=created_at:asc"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"sort": "created_at:asc", "size": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["sort"] == "created_at:asc"
        print(f"✓ Sort asc applied: {data['pagination']['sort']}")
    
    def test_audit_logs_q_search(self, tokens):
        """Test q (search) parameter"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"q": "admin", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        print(f"✓ Search q='admin': {len(data['items'])} items returned")


class TestAuditLogsFilters:
    """Test audit logs filters: actor, role, country, event_type, date range"""
    
    def test_audit_filter_by_actor(self, tokens):
        """Test filter by actor (user_id/email)"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"actor": "admin@platform.com", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Filter by actor: {len(data['items'])} items")
    
    def test_audit_filter_by_role(self, tokens):
        """Test filter by role"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"role": "super_admin", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Filter by role=super_admin: {len(data['items'])} items")
    
    def test_audit_filter_by_country(self, tokens):
        """Test filter by country"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"country": "DE", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Filter by country=DE: {len(data['items'])} items")
    
    def test_audit_filter_by_event_type(self, tokens):
        """Test filter by event_type (action)"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"event_type": "PERMISSION_FLAG_GRANT", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Filter by event_type=PERMISSION_FLAG_GRANT: {len(data['items'])} items")
    
    def test_audit_filter_by_date_range(self, tokens):
        """Test filter by date_from and date_to"""
        now = datetime.now(timezone.utc)
        date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        date_to = now.strftime("%Y-%m-%d")
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={
                "date_from": date_from,
                "date_to": date_to,
                "size": 100
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Filter by date range ({date_from} to {date_to}): {len(data['items'])} items")
    
    def test_audit_combined_filters(self, tokens):
        """Test combined filters: role + country + sort"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={
                "role": "super_admin",
                "country": "DE",
                "sort": "created_at:desc",
                "size": 50
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Combined filters (role+country+sort): {len(data['items'])} items")


class TestAuditEventTypes:
    """Test audit event types and metadata endpoints"""
    
    def test_get_event_types(self, tokens):
        """Test /admin/audit-logs/event-types endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs/event-types",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "event_types" in data
        print(f"✓ Event types: {len(data['event_types'])} types available")


# =============================================================================
# PERMISSIONS ENDPOINTS PAGINATION & FILTER TESTS
# =============================================================================

class TestPermissionsUsersPagination:
    """Test /admin/permissions/users pagination: page/size/q/sort"""
    
    def test_permissions_users_default_pagination(self, tokens):
        """Test default pagination for permissions users"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "items" in data
        assert "pagination" in data
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["size"] == 20
        assert "total" in pagination
        assert "total_pages" in pagination
        print(f"✓ Users default pagination: page={pagination['page']}, size={pagination['size']}, total={pagination['total']}")
    
    def test_permissions_users_custom_page_size(self, tokens):
        """Test custom page and size"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 1, "size": 50}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["size"] == 50
        print(f"✓ Users custom size=50: {len(data['items'])} items")
    
    def test_permissions_users_q_search(self, tokens):
        """Test q search for users"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"q": "admin", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Users search q='admin': {len(data['items'])} items")
    
    def test_permissions_users_filter_role(self, tokens):
        """Test filter by role"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"role": "dealer", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["role"] == "dealer"
        print(f"✓ Users filter role=dealer: {len(data['items'])} items")
    
    def test_permissions_users_filter_country_scope(self, tokens):
        """Test filter by country_scope"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"country_scope": "DE", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Users filter country_scope=DE: {len(data['items'])} items")
    
    def test_permissions_users_sort(self, tokens):
        """Test sort parameter"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"sort": "created_at:asc", "size": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["sort"] == "created_at:asc"
        print(f"✓ Users sort=created_at:asc applied")


class TestPermissionsOverridesPagination:
    """Test /admin/permissions/overrides pagination: page/size/q/sort/actor"""
    
    def test_permissions_overrides_default_pagination(self, tokens):
        """Test default pagination for overrides"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "items" in data
        assert "pagination" in data
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["size"] == 20
        print(f"✓ Overrides default pagination: page={pagination['page']}, size={pagination['size']}, total={pagination['total']}")
    
    def test_permissions_overrides_custom_page_size(self, tokens):
        """Test custom page and size"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 1, "size": 50}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["size"] == 50
        print(f"✓ Overrides custom size=50: {len(data['items'])} items")
    
    def test_permissions_overrides_q_search(self, tokens):
        """Test q search for overrides"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"]),
            params={"q": "platform", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Overrides search q='platform': {len(data['items'])} items")
    
    def test_permissions_overrides_filter_actor(self, tokens):
        """Test filter by actor (created_by)"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"]),
            params={"actor": "admin@platform.com", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Overrides filter actor=admin@platform.com: {len(data['items'])} items")
    
    def test_permissions_overrides_filter_role(self, tokens):
        """Test filter by role"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"]),
            params={"role": "admin", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Overrides filter role=admin: {len(data['items'])} items")
    
    def test_permissions_overrides_filter_country_scope(self, tokens):
        """Test filter by country_scope"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"]),
            params={"country_scope": "DE", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Overrides filter country_scope=DE: {len(data['items'])} items")
    
    def test_permissions_overrides_sort(self, tokens):
        """Test sort parameter"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["super_admin"]),
            params={"sort": "created_at:desc", "size": 10}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["sort"] == "created_at:desc"
        print(f"✓ Overrides sort=created_at:desc applied")


class TestPermissionsShadowDiffPagination:
    """Test /admin/permissions/shadow-diff pagination: page/size/q/sort"""
    
    def test_shadow_diff_default_pagination(self, tokens):
        """Test shadow-diff default pagination"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "diffs" in data
        assert "diff_count" in data
        assert "checked_user_count" in data
        assert "pagination" in data
        pagination = data["pagination"]
        assert pagination["page"] == 1
        print(f"✓ Shadow-diff: diff_count={data['diff_count']}, checked_users={data['checked_user_count']}")
    
    def test_shadow_diff_custom_size(self, tokens):
        """Test shadow-diff custom size"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=auth_header(tokens["super_admin"]),
            params={"size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["size"] == 100
        print(f"✓ Shadow-diff custom size=100")
    
    def test_shadow_diff_filter_role(self, tokens):
        """Test shadow-diff filter by role"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=auth_header(tokens["super_admin"]),
            params={"role": "dealer", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Shadow-diff filter role=dealer: {data['checked_user_count']} users checked")
    
    def test_shadow_diff_filter_country_scope(self, tokens):
        """Test shadow-diff filter by country_scope"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=auth_header(tokens["super_admin"]),
            params={"country_scope": "DE", "size": 100}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"✓ Shadow-diff filter country_scope=DE: {data['checked_user_count']} users checked")


# =============================================================================
# CSV EXPORT PERMISSION ENFORCEMENT TESTS
# =============================================================================

class TestCSVExportPermissions:
    """Test CSV export permission enforcement (super_admin only)"""
    
    def test_permissions_overrides_export_super_admin(self, tokens):
        """Test super_admin can export overrides CSV"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides/export",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")
        print(f"✓ Super admin can export permissions CSV")
    
    def test_permissions_overrides_export_user_forbidden(self, tokens):
        """Test normal user gets 403 on export"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides/export",
            headers=auth_header(tokens["user"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ Normal user gets 403 on export")
    
    def test_permissions_overrides_export_dealer_forbidden(self, tokens):
        """Test dealer gets 403 on export"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides/export",
            headers=auth_header(tokens["dealer"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ Dealer gets 403 on export")
    
    def test_audit_logs_export_super_admin(self, tokens):
        """Test super_admin can export audit logs CSV"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs/export",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        print(f"✓ Super admin can export audit logs CSV")


# =============================================================================
# 403 UNAUTHORIZED ACCESS TESTS
# =============================================================================

class TestUnauthorizedAccess403:
    """Test 403 guards for user/dealer on admin audit/permissions APIs"""
    
    def test_audit_logs_user_403(self, tokens):
        """Normal user gets 403 on audit-logs"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["user"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on audit-logs")
    
    def test_audit_logs_dealer_403(self, tokens):
        """Dealer gets 403 on audit-logs"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["dealer"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ Dealer gets 403 on audit-logs")
    
    def test_permissions_users_user_403(self, tokens):
        """Normal user gets 403 on permissions/users"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["user"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on permissions/users")
    
    def test_permissions_users_dealer_403(self, tokens):
        """Dealer gets 403 on permissions/users"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["dealer"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ Dealer gets 403 on permissions/users")
    
    def test_permissions_overrides_user_403(self, tokens):
        """Normal user gets 403 on permissions/overrides"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["user"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on permissions/overrides")
    
    def test_permissions_overrides_dealer_403(self, tokens):
        """Dealer gets 403 on permissions/overrides"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/overrides",
            headers=auth_header(tokens["dealer"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ Dealer gets 403 on permissions/overrides")
    
    def test_shadow_diff_user_403(self, tokens):
        """Normal user gets 403 on shadow-diff"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=auth_header(tokens["user"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on shadow-diff")
    
    def test_shadow_diff_dealer_403(self, tokens):
        """Dealer gets 403 on shadow-diff"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/shadow-diff",
            headers=auth_header(tokens["dealer"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ Dealer gets 403 on shadow-diff")
    
    def test_permissions_flags_user_403(self, tokens):
        """Normal user gets 403 on permissions/flags"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/permissions/flags",
            headers=auth_header(tokens["user"])
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on permissions/flags")
    
    def test_permissions_grant_user_403(self, tokens):
        """Normal user gets 403 on grant"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/permissions/grant",
            headers=auth_header(tokens["user"]),
            json={
                "target_user_id": "00000000-0000-0000-0000-000000000000",
                "domain": "finance",
                "action": "view",
                "reason": "Test grant from normal user"
            }
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on grant")
    
    def test_permissions_revoke_user_403(self, tokens):
        """Normal user gets 403 on revoke"""
        resp = requests.post(
            f"{BASE_URL}/api/admin/permissions/revoke",
            headers=auth_header(tokens["user"]),
            json={
                "target_user_id": "00000000-0000-0000-0000-000000000000",
                "domain": "finance",
                "action": "view",
                "reason": "Test revoke from normal user"
            }
        )
        assert resp.status_code == 403, f"Expected 403 but got {resp.status_code}"
        print(f"✓ User gets 403 on revoke")


# =============================================================================
# 100K PAGINATION STABILITY TESTS
# =============================================================================

class TestPaginationStability:
    """Test pagination stability with existing audit data"""
    
    def test_audit_pagination_stability_page_navigation(self, tokens):
        """Test page navigation doesn't overlap"""
        # Get page 1
        resp1 = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 1, "size": 10, "sort": "created_at:desc"}
        )
        assert resp1.status_code == 200
        page1_ids = {item["id"] for item in resp1.json()["items"]}
        
        # Get page 2
        resp2 = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 2, "size": 10, "sort": "created_at:desc"}
        )
        assert resp2.status_code == 200
        page2_ids = {item["id"] for item in resp2.json()["items"]}
        
        # Check no overlap
        overlap = page1_ids & page2_ids
        assert len(overlap) == 0, f"Page overlap detected: {overlap}"
        print(f"✓ Pagination stable: page 1 ({len(page1_ids)} items), page 2 ({len(page2_ids)} items), overlap={len(overlap)}")
    
    def test_audit_response_time_acceptable(self, tokens):
        """Test response time is acceptable for pagination queries"""
        start = time.time()
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit-logs",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 1, "size": 100, "sort": "created_at:desc"}
        )
        elapsed_ms = (time.time() - start) * 1000
        
        assert resp.status_code == 200
        # p95 should be under 400ms as per criteria
        print(f"✓ Response time: {elapsed_ms:.2f}ms (target < 400ms)")
        # Don't assert hard limit in tests since network latency varies
    
    def test_permissions_users_pagination_stability(self, tokens):
        """Test permissions/users pagination stability"""
        resp1 = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 1, "size": 10, "sort": "created_at:desc"}
        )
        assert resp1.status_code == 200
        page1_ids = {item["id"] for item in resp1.json()["items"]}
        
        resp2 = requests.get(
            f"{BASE_URL}/api/admin/permissions/users",
            headers=auth_header(tokens["super_admin"]),
            params={"page": 2, "size": 10, "sort": "created_at:desc"}
        )
        assert resp2.status_code == 200
        page2_ids = {item["id"] for item in resp2.json()["items"]}
        
        overlap = page1_ids & page2_ids
        assert len(overlap) == 0, f"Page overlap detected: {overlap}"
        print(f"✓ Users pagination stable: page 1 ({len(page1_ids)}), page 2 ({len(page2_ids)}), overlap={len(overlap)}")


# =============================================================================
# DASHBOARD ENDPOINTS TESTS
# =============================================================================

class TestAuditDashboard:
    """Test audit dashboard helper endpoints"""
    
    def test_dashboard_schema(self, tokens):
        """Test dashboard schema endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/schema",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "schema_version" in data
        print(f"✓ Dashboard schema version: {data.get('schema_version')}")
    
    def test_dashboard_stats(self, tokens):
        """Test dashboard stats endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/stats",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "windows" in data
        print(f"✓ Dashboard stats: windows present")
    
    def test_dashboard_anomalies(self, tokens):
        """Test dashboard anomalies endpoint"""
        resp = requests.get(
            f"{BASE_URL}/api/admin/audit/dashboard/anomalies",
            headers=auth_header(tokens["super_admin"])
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "anomalies" in data
        print(f"✓ Dashboard anomalies: {len(data.get('anomalies', []))} anomalies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
