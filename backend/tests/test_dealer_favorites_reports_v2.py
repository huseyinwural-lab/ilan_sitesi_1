"""
Tests for Dealer Favorites, Reports, Messages, and Customers endpoints.
Testing iteration 37: Kurumsal row2 menu, Favorites, Reports, Messages read status
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Failed to authenticate dealer: {response.text}")
    data = response.json()
    return data.get("access_token")


class TestDealerFavoritesEndpoint:
    """GET /api/dealer/favorites endpoint tests"""

    def test_favorites_requires_auth(self):
        """Test that favorites endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dealer/favorites")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Favorites endpoint requires authentication")

    def test_favorites_response_shape(self, dealer_token):
        """Test favorites endpoint returns correct response shape"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        # Check response contains required keys
        assert "favorite_listings" in data, "Missing favorite_listings"
        assert "favorite_searches" in data, "Missing favorite_searches"
        assert "favorite_sellers" in data, "Missing favorite_sellers"
        assert "summary" in data, "Missing summary"
        
        # Check lists are actually lists
        assert isinstance(data["favorite_listings"], list), "favorite_listings should be a list"
        assert isinstance(data["favorite_searches"], list), "favorite_searches should be a list"
        assert isinstance(data["favorite_sellers"], list), "favorite_sellers should be a list"
        
        # Check summary has correct shape
        summary = data["summary"]
        assert "favorite_listings_count" in summary, "Missing favorite_listings_count in summary"
        assert "favorite_searches_count" in summary, "Missing favorite_searches_count in summary"
        assert "favorite_sellers_count" in summary, "Missing favorite_sellers_count in summary"

        print(f"PASS: Favorites response shape correct - {len(data['favorite_listings'])} listings, {len(data['favorite_searches'])} searches, {len(data['favorite_sellers'])} sellers")

    def test_favorites_listings_item_shape(self, dealer_token):
        """Test favorite_listings items have correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are favorite listings, check their shape
        if data["favorite_listings"]:
            item = data["favorite_listings"][0]
            expected_keys = ["listing_id", "title", "city", "price", "favorite_count", "last_favorited_at", "route"]
            for key in expected_keys:
                assert key in item, f"Missing key '{key}' in favorite_listings item"
            print(f"PASS: Favorite listing item has all required fields: {list(item.keys())}")
        else:
            print("INFO: No favorite listings to check shape")

    def test_favorites_searches_item_shape(self, dealer_token):
        """Test favorite_searches items have correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are favorite searches, check their shape
        if data["favorite_searches"]:
            item = data["favorite_searches"][0]
            expected_keys = ["search_key", "label", "search_count", "last_seen_at", "route"]
            for key in expected_keys:
                assert key in item, f"Missing key '{key}' in favorite_searches item"
            print(f"PASS: Favorite search item has all required fields: {list(item.keys())}")
        else:
            print("INFO: No favorite searches to check shape")

    def test_favorites_sellers_item_shape(self, dealer_token):
        """Test favorite_sellers items have correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # If there are favorite sellers, check their shape
        if data["favorite_sellers"]:
            item = data["favorite_sellers"][0]
            expected_keys = ["user_id", "full_name", "email", "favorite_count", "last_favorited_at", "route"]
            for key in expected_keys:
                assert key in item, f"Missing key '{key}' in favorite_sellers item"
            print(f"PASS: Favorite seller item has all required fields: {list(item.keys())}")
        else:
            print("INFO: No favorite sellers to check shape")


class TestDealerReportsEndpoint:
    """GET /api/dealer/reports endpoint tests"""

    def test_reports_requires_auth(self):
        """Test that reports endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dealer/reports")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Reports endpoint requires authentication")

    def test_reports_default_30_days(self, dealer_token):
        """Test reports endpoint with default 30 days window"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check response contains required keys
        assert "kpis" in data, "Missing kpis"
        assert "filters" in data, "Missing filters"
        assert "report_sections" in data, "Missing report_sections"
        assert "package_reports" in data, "Missing package_reports"
        assert "doping_usage_report" in data, "Missing doping_usage_report"
        
        print(f"PASS: Reports response has all required top-level keys")

    def test_reports_window_7_days(self, dealer_token):
        """Test reports endpoint with 7 days window"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=7",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["window_days"] == 7
        print("PASS: Reports endpoint accepts window_days=7")

    def test_reports_window_14_days(self, dealer_token):
        """Test reports endpoint with 14 days window"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=14",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["window_days"] == 14
        print("PASS: Reports endpoint accepts window_days=14")

    def test_reports_window_30_days(self, dealer_token):
        """Test reports endpoint with 30 days window"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["window_days"] == 30
        print("PASS: Reports endpoint accepts window_days=30")

    def test_reports_window_90_days(self, dealer_token):
        """Test reports endpoint with 90 days window"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=90",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["window_days"] == 90
        print("PASS: Reports endpoint accepts window_days=90")

    def test_reports_window_31_days_rejected(self, dealer_token):
        """Test reports endpoint rejects window_days=31"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=31",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Reports endpoint rejects window_days=31 with 400")

    def test_reports_window_15_days_rejected(self, dealer_token):
        """Test reports endpoint rejects window_days=15 (not in allowed list)"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=15",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Reports endpoint rejects window_days=15 with 400")

    def test_reports_kpis_structure(self, dealer_token):
        """Test reports KPIs have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        kpis = data["kpis"]
        assert "views_7d" in kpis, "Missing views_7d in kpis"
        assert "contact_clicks_7d" in kpis, "Missing contact_clicks_7d in kpis"
        assert isinstance(kpis["views_7d"], int), "views_7d should be integer"
        assert isinstance(kpis["contact_clicks_7d"], int), "contact_clicks_7d should be integer"
        
        print(f"PASS: KPIs structure correct - views_7d: {kpis['views_7d']}, contact_clicks_7d: {kpis['contact_clicks_7d']}")

    def test_reports_sections_structure(self, dealer_token):
        """Test report_sections have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        report_sections = data["report_sections"]
        expected_sections = [
            "listing_report", "views_report", "favorites_report", 
            "messages_report", "mobile_calls_report"
        ]
        
        for section_key in expected_sections:
            assert section_key in report_sections, f"Missing {section_key} in report_sections"
            section = report_sections[section_key]
            assert "title" in section, f"Missing title in {section_key}"
            assert "current_value" in section, f"Missing current_value in {section_key}"
            assert "previous_value" in section, f"Missing previous_value in {section_key}"
            assert "change_pct" in section, f"Missing change_pct in {section_key}"
            assert "total" in section, f"Missing total in {section_key}"
            assert "series" in section, f"Missing series in {section_key}"
            assert isinstance(section["series"], list), f"series in {section_key} should be a list"
        
        print(f"PASS: All 5 report sections have correct structure")

    def test_reports_package_reports_structure(self, dealer_token):
        """Test package_reports have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        pkg = data["package_reports"]
        assert "package_name" in pkg, "Missing package_name"
        assert "period" in pkg, "Missing period"
        assert "used" in pkg, "Missing used"
        assert "remaining" in pkg, "Missing remaining"
        assert "quota_limit" in pkg, "Missing quota_limit"
        assert "usage_rows" in pkg, "Missing usage_rows"
        
        print(f"PASS: package_reports structure correct - used: {pkg['used']}, remaining: {pkg['remaining']}, quota: {pkg['quota_limit']}")

    def test_reports_doping_usage_structure(self, dealer_token):
        """Test doping_usage_report has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        doping = data["doping_usage_report"]
        assert "total_used" in doping, "Missing total_used"
        assert "total_views" in doping, "Missing total_views"
        assert "series_used" in doping, "Missing series_used"
        assert "series_views" in doping, "Missing series_views"
        
        print(f"PASS: doping_usage_report structure correct - total_used: {doping['total_used']}, total_views: {doping['total_views']}")


class TestDealerMessagesEndpoint:
    """GET /api/dealer/messages and POST /api/dealer/messages/{id}/read tests"""

    def test_messages_requires_auth(self):
        """Test that messages endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dealer/messages")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Messages endpoint requires authentication")

    def test_messages_response_shape(self, dealer_token):
        """Test messages endpoint returns correct response shape"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing items"
        assert "notification_items" in data, "Missing notification_items"
        assert "summary" in data, "Missing summary"
        
        # Check summary structure
        summary = data["summary"]
        assert "listing_messages" in summary, "Missing listing_messages in summary"
        assert "notifications" in summary, "Missing notifications in summary"
        assert "unread_listing_messages" in summary, "Missing unread_listing_messages in summary"
        
        print(f"PASS: Messages response shape correct - {summary['listing_messages']} messages, {summary['unread_listing_messages']} unread")

    def test_messages_items_have_unread_count(self, dealer_token):
        """Test message items have unread_count field"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            item = data["items"][0]
            assert "unread_count" in item, "Missing unread_count in message item"
            assert "read_status" in item or "unread_count" in item, "Missing read indicator in message item"
            print(f"PASS: Message item has unread_count: {item.get('unread_count')}")
        else:
            print("INFO: No message items to check unread_count")

    def test_messages_items_have_required_fields(self, dealer_token):
        """Test message items have all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            item = data["items"][0]
            expected_keys = [
                "conversation_id", "listing_id", "buyer_id", 
                "message_count", "unread_count", "last_message", "last_message_at"
            ]
            for key in expected_keys:
                assert key in item, f"Missing key '{key}' in message item"
            print(f"PASS: Message item has all required fields")
        else:
            print("INFO: No message items to check fields")

    def test_mark_read_invalid_uuid(self, dealer_token):
        """Test mark read endpoint with invalid UUID"""
        response = requests.post(
            f"{BASE_URL}/api/dealer/messages/invalid-uuid/read",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("PASS: Mark read rejects invalid UUID")

    def test_mark_read_not_found(self, dealer_token):
        """Test mark read endpoint with non-existent conversation"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/dealer/messages/{fake_uuid}/read",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code in [404, 403], f"Expected 404/403, got {response.status_code}"
        print(f"PASS: Mark read returns {response.status_code} for non-existent conversation")


class TestDealerCustomersEndpoint:
    """GET /api/dealer/customers endpoint tests"""

    def test_customers_requires_auth(self):
        """Test that customers endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dealer/customers")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Customers endpoint requires authentication")

    def test_customers_response_shape(self, dealer_token):
        """Test customers endpoint returns correct response shape"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "items" in data, "Missing items"
        assert "non_store_users" in data, "Missing non_store_users"
        assert "summary" in data, "Missing summary"
        
        # Check summary structure
        summary = data["summary"]
        assert "users_count" in summary, "Missing users_count in summary"
        assert "non_store_users_count" in summary, "Missing non_store_users_count in summary"
        
        print(f"PASS: Customers response shape correct - {summary['users_count']} users, {summary['non_store_users_count']} non-store users")

    def test_customers_items_structure(self, dealer_token):
        """Test customer items have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            item = data["items"][0]
            expected_keys = [
                "customer_id", "customer_email", "customer_name", 
                "customer_status", "customer_is_active"
            ]
            for key in expected_keys:
                assert key in item, f"Missing key '{key}' in customer item"
            print(f"PASS: Customer item has all required fields")
        else:
            print("INFO: No customer items to check structure")

    def test_customers_non_store_users_structure(self, dealer_token):
        """Test non_store_users items have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["non_store_users"]:
            item = data["non_store_users"][0]
            expected_keys = ["user_id", "full_name", "email", "status", "is_active"]
            for key in expected_keys:
                assert key in item, f"Missing key '{key}' in non_store_user item"
            print(f"PASS: Non-store user item has all required fields")
        else:
            print("INFO: No non-store users to check structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
