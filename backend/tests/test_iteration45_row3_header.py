"""
Iteration 45: Testing Dealer Header Row3 Layout
- Backend: /api/dealer/portal/config header_row3_controls fields
- Frontend: Row3 layout (user on left, store filter -> page edit -> announcements on right)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEALER_EMAIL = "dealer1772201722@example.com"
DEALER_PASSWORD = "Dealer123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def dealer_token(api_client):
    """Get dealer authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEALER_EMAIL,
        "password": DEALER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    # Fallback to default dealer
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": "dealer@platform.com",
        "password": "Dealer123!"
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Dealer authentication failed - skipping tests")


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed - skipping tests")


class TestDealerPortalConfigRow3:
    """Test dealer portal config endpoint returns row3 controls correctly"""

    def test_portal_config_returns_header_row3_controls(self, api_client, dealer_token):
        """Verify /api/dealer/portal/config returns header_row3_controls object"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "header_row3_controls" in data, "Missing header_row3_controls in response"
        
        row3 = data["header_row3_controls"]
        assert isinstance(row3, dict), "header_row3_controls should be a dict"
        print(f"header_row3_controls: {row3}")

    def test_row3_has_page_edit_enabled_field(self, api_client, dealer_token):
        """Verify row3 controls contain page_edit_enabled"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        assert "page_edit_enabled" in row3, "Missing page_edit_enabled in header_row3_controls"
        assert isinstance(row3["page_edit_enabled"], bool), "page_edit_enabled should be boolean"
        print(f"page_edit_enabled: {row3['page_edit_enabled']}")

    def test_row3_has_announcements_enabled_field(self, api_client, dealer_token):
        """Verify row3 controls contain announcements_enabled"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        assert "announcements_enabled" in row3, "Missing announcements_enabled in header_row3_controls"
        assert isinstance(row3["announcements_enabled"], bool), "announcements_enabled should be boolean"
        print(f"announcements_enabled: {row3['announcements_enabled']}")

    def test_row3_has_user_display_name_field(self, api_client, dealer_token):
        """Verify row3 controls contain user_display_name"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        assert "user_display_name" in row3, "Missing user_display_name in header_row3_controls"
        assert isinstance(row3["user_display_name"], str), "user_display_name should be string"
        assert len(row3["user_display_name"]) > 0, "user_display_name should not be empty"
        print(f"user_display_name: {row3['user_display_name']}")

    def test_row3_has_stores_field(self, api_client, dealer_token):
        """Verify row3 controls contain stores list"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        assert "stores" in row3, "Missing stores in header_row3_controls"
        assert isinstance(row3["stores"], list), "stores should be a list"
        
        stores = row3["stores"]
        assert len(stores) >= 1, "stores should have at least one item (Tümü)"
        
        # Check that first item is 'all' / 'Tümü'
        first_store = stores[0]
        assert first_store.get("key") == "all", "First store key should be 'all'"
        assert first_store.get("label") == "Tümü", "First store label should be 'Tümü'"
        print(f"stores: {stores}")

    def test_row3_has_store_filter_enabled_field(self, api_client, dealer_token):
        """Verify row3 controls contain store_filter_enabled"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        assert "store_filter_enabled" in row3, "Missing store_filter_enabled in header_row3_controls"
        assert isinstance(row3["store_filter_enabled"], bool), "store_filter_enabled should be boolean"
        print(f"store_filter_enabled: {row3['store_filter_enabled']}")

    def test_row3_has_user_dropdown_enabled_field(self, api_client, dealer_token):
        """Verify row3 controls contain user_dropdown_enabled"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        assert "user_dropdown_enabled" in row3, "Missing user_dropdown_enabled in header_row3_controls"
        assert isinstance(row3["user_dropdown_enabled"], bool), "user_dropdown_enabled should be boolean"
        print(f"user_dropdown_enabled: {row3['user_dropdown_enabled']}")

    def test_row3_complete_response_structure(self, api_client, dealer_token):
        """Verify complete header_row3_controls structure"""
        response = api_client.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        
        row3 = response.json().get("header_row3_controls", {})
        
        # All required fields
        required_fields = [
            "store_filter_enabled",
            "user_dropdown_enabled", 
            "page_edit_enabled",
            "announcements_enabled",
            "user_display_name",
            "stores",
            "default_store_key"
        ]
        
        for field in required_fields:
            assert field in row3, f"Missing required field: {field}"
            print(f"  {field}: {row3[field]}")
        
        print("\n--- Complete header_row3_controls structure verified ---")


class TestAdminDealerPortalPreview:
    """Test admin dealer portal preview endpoint"""
    
    def test_admin_preview_returns_row3_controls(self, api_client, admin_token):
        """Verify admin preview also returns header_row3_controls"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/dealer-portal/config/preview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "header_row3_controls" in data, "Missing header_row3_controls in admin preview"
        
        row3 = data["header_row3_controls"]
        assert "page_edit_enabled" in row3
        assert "announcements_enabled" in row3
        assert "user_display_name" in row3
        assert "stores" in row3
        print(f"Admin preview header_row3_controls: {row3}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
