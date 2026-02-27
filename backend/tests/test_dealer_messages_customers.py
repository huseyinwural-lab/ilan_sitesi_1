"""
Test cases for Dealer Messages and Customers endpoints
Testing Features:
- GET /api/dealer/messages: items with unread_count/read_status, summary with unread_listing_messages
- POST /api/dealer/messages/{conversation_id}/read: mark unread messages as read
- GET /api/dealer/customers: tabs (users, non_store_users), filters, summary
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "dealer@platform.com", "password": "Dealer123!"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Dealer authentication failed")


@pytest.fixture
def dealer_headers(dealer_token):
    """Headers with dealer auth token"""
    return {
        "Authorization": f"Bearer {dealer_token}",
        "Content-Type": "application/json"
    }


class TestDealerMessages:
    """Test /api/dealer/messages endpoint"""

    def test_get_messages_returns_200(self, dealer_headers):
        """GET /api/dealer/messages returns 200"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages", headers=dealer_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/dealer/messages returns 200")

    def test_get_messages_has_items_field(self, dealer_headers):
        """GET /api/dealer/messages has items field"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages", headers=dealer_headers)
        data = response.json()
        assert "items" in data, "Response must have 'items' field"
        assert isinstance(data["items"], list), "'items' must be a list"
        print("✓ Response has 'items' field (list)")

    def test_get_messages_has_notification_items(self, dealer_headers):
        """GET /api/dealer/messages has notification_items field"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages", headers=dealer_headers)
        data = response.json()
        assert "notification_items" in data, "Response must have 'notification_items' field"
        assert isinstance(data["notification_items"], list), "'notification_items' must be a list"
        print("✓ Response has 'notification_items' field (list)")

    def test_get_messages_summary_has_required_fields(self, dealer_headers):
        """GET /api/dealer/messages summary has listing_messages, notifications, unread_listing_messages"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages", headers=dealer_headers)
        data = response.json()
        assert "summary" in data, "Response must have 'summary' field"
        summary = data["summary"]
        assert "listing_messages" in summary, "Summary must have 'listing_messages'"
        assert "notifications" in summary, "Summary must have 'notifications'"
        assert "unread_listing_messages" in summary, "Summary must have 'unread_listing_messages'"
        print(f"✓ Summary has required fields: {list(summary.keys())}")

    def test_get_messages_items_structure(self, dealer_headers):
        """GET /api/dealer/messages items have correct structure with unread_count/read_status"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages", headers=dealer_headers)
        data = response.json()
        items = data.get("items", [])
        
        # If there are items, check their structure
        if items:
            first_item = items[0]
            required_fields = ["conversation_id", "listing_id", "buyer_id", "message_count", 
                             "unread_count", "read_status"]
            for field in required_fields:
                assert field in first_item, f"Item must have '{field}' field"
            print("✓ Items have required fields including unread_count and read_status")
        else:
            print("✓ No items - structure check skipped (no conversations)")

    def test_messages_unauthenticated_returns_401_or_403(self):
        """GET /api/dealer/messages without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated access blocked")


class TestMarkConversationRead:
    """Test POST /api/dealer/messages/{conversation_id}/read endpoint"""

    def test_invalid_uuid_returns_400(self, dealer_headers):
        """POST with invalid UUID returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/dealer/messages/invalid-uuid/read",
            headers=dealer_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "invalid" in response.json().get("detail", "").lower()
        print("✓ Invalid UUID returns 400")

    def test_nonexistent_conversation_returns_404(self, dealer_headers):
        """POST with non-existent conversation returns 404"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/dealer/messages/{fake_uuid}/read",
            headers=dealer_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent conversation returns 404")

    def test_mark_read_unauthenticated_returns_401_or_403(self):
        """POST without auth returns 401/403"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.post(f"{BASE_URL}/api/dealer/messages/{fake_uuid}/read")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated access blocked")


class TestDealerCustomers:
    """Test /api/dealer/customers endpoint"""

    def test_get_customers_returns_200(self, dealer_headers):
        """GET /api/dealer/customers returns 200"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers", headers=dealer_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/dealer/customers returns 200")

    def test_get_customers_has_items_field(self, dealer_headers):
        """GET /api/dealer/customers has items field"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers", headers=dealer_headers)
        data = response.json()
        assert "items" in data, "Response must have 'items' field"
        assert isinstance(data["items"], list), "'items' must be a list"
        print("✓ Response has 'items' field (list)")

    def test_get_customers_has_non_store_users(self, dealer_headers):
        """GET /api/dealer/customers has non_store_users field"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers", headers=dealer_headers)
        data = response.json()
        assert "non_store_users" in data, "Response must have 'non_store_users' field"
        assert isinstance(data["non_store_users"], list), "'non_store_users' must be a list"
        print("✓ Response has 'non_store_users' field (list)")

    def test_get_customers_summary_has_required_fields(self, dealer_headers):
        """GET /api/dealer/customers summary has users_count, non_store_users_count"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers", headers=dealer_headers)
        data = response.json()
        assert "summary" in data, "Response must have 'summary' field"
        summary = data["summary"]
        assert "users_count" in summary, "Summary must have 'users_count'"
        assert "non_store_users_count" in summary, "Summary must have 'non_store_users_count'"
        print(f"✓ Summary has required fields: {list(summary.keys())}")

    def test_get_customers_non_store_users_structure(self, dealer_headers):
        """GET /api/dealer/customers non_store_users have correct structure"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers", headers=dealer_headers)
        data = response.json()
        non_store_users = data.get("non_store_users", [])
        
        if non_store_users:
            first_user = non_store_users[0]
            required_fields = ["user_id", "full_name", "email", "status", "is_active"]
            for field in required_fields:
                assert field in first_user, f"Non-store user must have '{field}' field"
            print("✓ Non-store users have required fields")
        else:
            print("✓ No non-store users - structure check skipped")

    def test_customers_unauthenticated_returns_401_or_403(self):
        """GET /api/dealer/customers without auth returns 401/403"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated access blocked")


class TestDealerFavorites:
    """Test /api/dealer/favorites endpoint"""

    def test_get_favorites_returns_200(self, dealer_headers):
        response = requests.get(f"{BASE_URL}/api/dealer/favorites", headers=dealer_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/dealer/favorites returns 200")

    def test_get_favorites_has_expected_fields(self, dealer_headers):
        response = requests.get(f"{BASE_URL}/api/dealer/favorites", headers=dealer_headers)
        data = response.json()
        assert "favorite_listings" in data
        assert "favorite_searches" in data
        assert "favorite_sellers" in data
        assert "summary" in data
        print("✓ Favorites payload has expected fields")


class TestDealerReports:
    """Test /api/dealer/reports endpoint"""

    def test_get_reports_returns_200(self, dealer_headers):
        response = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=30", headers=dealer_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/dealer/reports returns 200")

    def test_reports_has_expected_blocks(self, dealer_headers):
        response = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=30", headers=dealer_headers)
        data = response.json()
        assert "kpis" in data
        assert "filters" in data
        assert "report_sections" in data
        assert "package_reports" in data
        assert "doping_usage_report" in data
        print("✓ Reports payload has expected blocks")

    def test_reports_invalid_window_returns_400(self, dealer_headers):
        response = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=31", headers=dealer_headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid window_days rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
