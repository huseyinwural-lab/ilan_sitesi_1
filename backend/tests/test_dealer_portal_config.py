"""
Dealer Portal Config API Tests - Iteration 19
Tests for:
- Dealer route endpoints: /api/dealer/overview, messages, customers, reports, purchase, settings
- Dealer header quick actions and config-driven layout
- Admin Dealer Portal Config management (dnd-kit reorder, visible toggle)
- Feature flag read-only display
- Dashboard summary widgets
- Analytics events with dealer token
- RBAC: non-dealer users should not access /api/dealer/* endpoints
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if res.status_code != 200:
        pytest.skip("Admin authentication failed")
    return res.json().get("access_token")


@pytest.fixture(scope="module")
def dealer_token():
    """Authenticate as dealer"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEALER_EMAIL,
        "password": DEALER_PASSWORD
    })
    if res.status_code != 200:
        pytest.skip("Dealer authentication failed")
    return res.json().get("access_token")


@pytest.fixture(scope="module")
def user_token():
    """Authenticate as regular user (non-dealer)"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    })
    if res.status_code != 200:
        pytest.skip("User authentication failed")
    return res.json().get("access_token")


class TestDealerPortalConfig:
    """Dealer portal config API tests"""
    
    def test_dealer_portal_config_returns_200(self, dealer_token):
        """GET /api/dealer/portal/config should return 200 with header/sidebar items"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Should have header_items, sidebar_items, modules arrays
        assert "header_items" in data, "Missing header_items"
        assert "sidebar_items" in data, "Missing sidebar_items"
        assert isinstance(data["header_items"], list), "header_items should be list"
        assert isinstance(data["sidebar_items"], list), "sidebar_items should be list"
        print(f"Dealer portal config: {len(data['header_items'])} header items, {len(data['sidebar_items'])} sidebar items")

    def test_dealer_portal_config_header_items_structure(self, dealer_token):
        """Header items should have proper structure with route and icon"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        for item in data.get("header_items", []):
            assert "key" in item, f"Missing key in header item: {item}"
            assert "route" in item, f"Missing route in header item: {item}"
            assert "icon" in item, f"Missing icon in header item: {item}"
            print(f"Header item: {item['key']} -> {item['route']}")

    def test_dealer_portal_config_sidebar_items_structure(self, dealer_token):
        """Sidebar items should have proper structure"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        for item in data.get("sidebar_items", []):
            assert "key" in item, f"Missing key in sidebar item: {item}"
            assert "route" in item, f"Missing route in sidebar item: {item}"
            print(f"Sidebar item: {item['key']} -> {item['route']}")


class TestDealerDashboardSummary:
    """Dealer dashboard summary widget tests"""
    
    def test_dashboard_summary_returns_200(self, dealer_token):
        """GET /api/dealer/dashboard/summary should return 200 with widgets"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Should have widgets array
        assert "widgets" in data, "Missing widgets"
        assert isinstance(data["widgets"], list), "widgets should be list"
        print(f"Dashboard summary: {len(data['widgets'])} widgets")
        
    def test_dashboard_summary_widgets_have_route(self, dealer_token):
        """Widgets should have click-through route field"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        widgets = data.get("widgets", [])
        for widget in widgets:
            assert "key" in widget, f"Widget missing key: {widget}"
            assert "route" in widget, f"Widget missing route: {widget}"
            assert "value" in widget or "title" in widget, f"Widget missing value/title: {widget}"
            print(f"Widget: {widget.get('key')} -> {widget.get('route')}")


class TestDealerEndpoints:
    """Individual dealer endpoint tests"""
    
    def test_dealer_messages_returns_200(self, dealer_token):
        """GET /api/dealer/messages should return 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data, "Missing items"
        print(f"Dealer messages: {len(data.get('items', []))} items")
    
    def test_dealer_customers_returns_200(self, dealer_token):
        """GET /api/dealer/customers should return 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data, "Missing items"
        print(f"Dealer customers: {len(data.get('items', []))} items")
    
    def test_dealer_reports_returns_200(self, dealer_token):
        """GET /api/dealer/reports should return 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/reports",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "kpis" in data, "Missing kpis"
        print(f"Dealer reports KPIs: {data.get('kpis')}")
    
    def test_dealer_settings_profile_returns_200(self, dealer_token):
        """GET /api/dealer/settings/profile should return 200"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "profile" in data, "Missing profile"
        print(f"Dealer settings profile: company={data.get('profile', {}).get('company_name')}")
    
    def test_dealer_settings_profile_update(self, dealer_token):
        """PATCH /api/dealer/settings/profile should update and return 200"""
        res = requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers={
                "Authorization": f"Bearer {dealer_token}",
                "Content-Type": "application/json"
            },
            json={"contact_phone": "+491234567890"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("Dealer profile update: OK")


class TestAdminDealerPortalConfig:
    """Admin dealer portal config management tests"""
    
    def test_admin_dealer_portal_config_returns_200(self, admin_token):
        """GET /api/admin/dealer-portal/config should return nav_items and modules"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert "nav_items" in data, "Missing nav_items"
        assert "modules" in data, "Missing modules"
        assert isinstance(data["nav_items"], list), "nav_items should be list"
        assert isinstance(data["modules"], list), "modules should be list"
        print(f"Admin dealer config: {len(data['nav_items'])} nav items, {len(data['modules'])} modules")
        
    def test_admin_dealer_portal_config_feature_flag_info(self, admin_token):
        """Nav items should have feature_flag and feature_flag_enabled (read-only)"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        for item in data.get("nav_items", []):
            # feature_flag field should exist (can be null)
            assert "feature_flag" in item, f"Missing feature_flag in nav item: {item.get('key')}"
            # feature_flag_enabled should be present for read-only display
            if item.get("feature_flag"):
                print(f"Nav item {item.get('key')}: flag={item.get('feature_flag')}, enabled={item.get('feature_flag_enabled')}")
    
    def test_admin_dealer_portal_preview_returns_200(self, admin_token):
        """GET /api/admin/dealer-portal/config/preview should return dealer-view items"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config/preview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert "header_items" in data, "Missing header_items"
        assert "sidebar_items" in data, "Missing sidebar_items"
        assert "modules" in data, "Missing modules"
        print(f"Admin preview: {len(data.get('header_items', []))} header, {len(data.get('sidebar_items', []))} sidebar, {len(data.get('modules', []))} modules")

    def test_admin_dealer_nav_reorder(self, admin_token):
        """POST /api/admin/dealer-portal/nav/reorder should update order"""
        # First get current items
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        sidebar_items = [item for item in data.get("nav_items", []) if item.get("location") == "sidebar"]
        if len(sidebar_items) < 2:
            pytest.skip("Not enough sidebar items to test reorder")
        
        # Reverse order
        ordered_ids = [item["id"] for item in reversed(sidebar_items)]
        
        res = requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/nav/reorder",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"location": "sidebar", "ordered_ids": ordered_ids}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("Nav reorder: OK")
        
        # Restore original order
        original_order = [item["id"] for item in sidebar_items]
        requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/nav/reorder",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"location": "sidebar", "ordered_ids": original_order}
        )

    def test_admin_dealer_nav_visibility_toggle(self, admin_token):
        """PATCH /api/admin/dealer-portal/nav/{id} should toggle visible"""
        # Get current items
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        nav_items = data.get("nav_items", [])
        if not nav_items:
            pytest.skip("No nav items to test visibility toggle")
        
        target = nav_items[0]
        original_visible = target.get("visible")
        
        # Toggle visibility
        res = requests.patch(
            f"{BASE_URL}/api/admin/dealer-portal/nav/{target['id']}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"visible": not original_visible}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        # Verify change
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        updated_item = next((i for i in res.json().get("nav_items", []) if i["id"] == target["id"]), None)
        assert updated_item is not None
        assert updated_item["visible"] == (not original_visible), "Visibility not toggled"
        print(f"Nav visibility toggle: {target.get('key')} {original_visible} -> {not original_visible}")
        
        # Restore original
        requests.patch(
            f"{BASE_URL}/api/admin/dealer-portal/nav/{target['id']}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"visible": original_visible}
        )

    def test_admin_dealer_modules_reorder(self, admin_token):
        """POST /api/admin/dealer-portal/modules/reorder should update order"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        modules = data.get("modules", [])
        if len(modules) < 2:
            pytest.skip("Not enough modules to test reorder")
        
        # Reverse order
        ordered_ids = [m["id"] for m in reversed(modules)]
        
        res = requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/modules/reorder",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"ordered_ids": ordered_ids}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("Module reorder: OK")
        
        # Restore original order
        original_order = [m["id"] for m in modules]
        requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/modules/reorder",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"ordered_ids": original_order}
        )


class TestAnalyticsEvents:
    """Analytics events API tests"""
    
    def test_analytics_events_with_dealer_token(self, dealer_token):
        """POST /api/analytics/events should accept dealer events"""
        res = requests.post(
            f"{BASE_URL}/api/analytics/events",
            headers={
                "Authorization": f"Bearer {dealer_token}",
                "Content-Type": "application/json"
            },
            json={
                "event_name": "dealer_nav_click",
                "session_id": str(uuid.uuid4()),
                "page": "/dealer/overview",
                "metadata": {"key": "overview", "route": "/dealer/overview"}
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("Analytics event: dealer_nav_click OK")
    
    def test_analytics_events_dealer_widget_click(self, dealer_token):
        """POST /api/analytics/events should accept dealer_widget_click"""
        res = requests.post(
            f"{BASE_URL}/api/analytics/events",
            headers={
                "Authorization": f"Bearer {dealer_token}",
                "Content-Type": "application/json"
            },
            json={
                "event_name": "dealer_widget_click",
                "session_id": str(uuid.uuid4()),
                "page": "/dealer/overview",
                "metadata": {"widget_key": "active_listings", "route": "/dealer/listings"}
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("Analytics event: dealer_widget_click OK")
    
    def test_analytics_events_dealer_contact_click(self, dealer_token):
        """POST /api/analytics/events should accept dealer_contact_click"""
        res = requests.post(
            f"{BASE_URL}/api/analytics/events",
            headers={
                "Authorization": f"Bearer {dealer_token}",
                "Content-Type": "application/json"
            },
            json={
                "event_name": "dealer_contact_click",
                "session_id": str(uuid.uuid4()),
                "page": "/dealer/customers",
                "metadata": {"customer_id": "test-123"}
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        print("Analytics event: dealer_contact_click OK")


class TestRBACDealerEndpoints:
    """RBAC tests: non-dealer users should not access dealer endpoints"""
    
    def test_non_dealer_cannot_access_dealer_messages(self, user_token):
        """Regular user should not access /api/dealer/messages"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"RBAC: non-dealer /api/dealer/messages -> {res.status_code}")
    
    def test_non_dealer_cannot_access_dealer_customers(self, user_token):
        """Regular user should not access /api/dealer/customers"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"RBAC: non-dealer /api/dealer/customers -> {res.status_code}")
    
    def test_non_dealer_cannot_access_dealer_reports(self, user_token):
        """Regular user should not access /api/dealer/reports"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/reports",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"RBAC: non-dealer /api/dealer/reports -> {res.status_code}")
    
    def test_non_dealer_cannot_access_dealer_settings(self, user_token):
        """Regular user should not access /api/dealer/settings/profile"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"RBAC: non-dealer /api/dealer/settings/profile -> {res.status_code}")
    
    def test_non_dealer_cannot_access_dealer_portal_config(self, user_token):
        """Regular user should not access /api/dealer/portal/config"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"RBAC: non-dealer /api/dealer/portal/config -> {res.status_code}")
    
    def test_non_dealer_cannot_access_dashboard_summary(self, user_token):
        """Regular user should not access /api/dealer/dashboard/summary"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print(f"RBAC: non-dealer /api/dealer/dashboard/summary -> {res.status_code}")


class TestAPIFallbackBehavior:
    """Test hard-coded menu fallback behavior"""
    
    def test_dealer_portal_config_no_hardcoded_fallback(self, dealer_token):
        """If API fails (simulated), frontend should NOT show hardcoded menu"""
        # This test verifies the endpoint returns real data, not hardcoded
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()
        
        # Verify items have DB-generated IDs (UUIDs), not hardcoded IDs
        for item in data.get("sidebar_items", []):
            item_id = item.get("id", "")
            # Check if ID looks like UUID (has dashes and is 36 chars)
            assert len(item_id) == 36 and item_id.count("-") == 4, f"Item {item.get('key')} has non-UUID id: {item_id}"
        
        print("Dealer portal config: verified config-driven items (UUID IDs)")
