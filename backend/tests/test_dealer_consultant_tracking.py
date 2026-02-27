"""
Test suite for iteration 38 - Dealer Consultant Tracking endpoint verification.
Tests new consultant-tracking endpoint and regression for favorites/reports/messages/customers.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer authentication token"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEALER_EMAIL,
        "password": DEALER_PASSWORD,
    })
    if res.status_code == 200:
        return res.json().get("access_token")
    pytest.skip(f"Dealer login failed: {res.status_code} - {res.text}")


@pytest.fixture(scope="module")
def dealer_headers(dealer_token):
    """Headers with dealer token"""
    return {"Authorization": f"Bearer {dealer_token}", "Content-Type": "application/json"}


# =================== GET /api/dealer/consultant-tracking tests ===================

class TestDealerConsultantTracking:
    """Consultant Tracking endpoint tests"""
    
    def test_consultant_tracking_default_sort(self, dealer_headers):
        """Test GET /api/dealer/consultant-tracking with default sort_by"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking", headers=dealer_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # Verify response structure - consultants
        assert "consultants" in data, "Missing 'consultants' in response"
        assert isinstance(data["consultants"], list), "consultants must be a list"
        
        # Verify response structure - evaluations
        assert "evaluations" in data, "Missing 'evaluations' in response"
        assert isinstance(data["evaluations"], list), "evaluations must be a list"
        
        # Verify response structure - summary
        assert "summary" in data, "Missing 'summary' in response"
        assert "consultants_count" in data["summary"], "Missing 'consultants_count' in summary"
        assert "evaluations_count" in data["summary"], "Missing 'evaluations_count' in summary"
        
        print(f"Consultants count: {data['summary']['consultants_count']}")
        print(f"Evaluations count: {data['summary']['evaluations_count']}")
    
    def test_consultant_tracking_consultant_shape(self, dealer_headers):
        """Test that consultant objects have correct shape"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        
        if len(data["consultants"]) > 0:
            consultant = data["consultants"][0]
            # Required fields in consultant object
            required_fields = [
                "consultant_id", "full_name", "email", "role", "is_active",
                "active_listing_count", "listing_count", "message_count",
                "message_count_7d", "message_change_7d", "message_change_label",
                "service_score", "review_count", "detail_route"
            ]
            for field in required_fields:
                assert field in consultant, f"Missing '{field}' in consultant object"
            
            # Type checks
            assert isinstance(consultant["consultant_id"], str)
            assert isinstance(consultant["service_score"], (int, float))
            assert isinstance(consultant["message_change_label"], str)
            print(f"Sample consultant: {consultant['full_name']} - Score: {consultant['service_score']}")
    
    def test_consultant_tracking_evaluation_shape(self, dealer_headers):
        """Test that evaluation objects have correct shape"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        
        if len(data["evaluations"]) > 0:
            evaluation = data["evaluations"][0]
            # Required fields in evaluation object
            required_fields = [
                "evaluation_id", "consultant_id", "consultant_name",
                "username", "evaluation_date", "score", "comment"
            ]
            for field in required_fields:
                assert field in evaluation, f"Missing '{field}' in evaluation object"
            
            assert isinstance(evaluation["score"], (int, float))
            print(f"Sample evaluation: score={evaluation['score']} by {evaluation['username']}")
    
    def test_consultant_tracking_sort_by_rating_desc(self, dealer_headers):
        """Test sort_by=rating_desc (default)"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=rating_desc", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        consultants = data.get("consultants", [])
        # If multiple consultants, verify sorted by score descending
        if len(consultants) >= 2:
            scores = [c.get("service_score", 0) for c in consultants]
            assert scores == sorted(scores, reverse=True), "Not sorted by rating_desc"
            print(f"Sorted scores (rating_desc): {scores[:5]}")
    
    def test_consultant_tracking_sort_by_name_asc(self, dealer_headers):
        """Test sort_by=name_asc"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=name_asc", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        consultants = data.get("consultants", [])
        # If multiple consultants, verify sorted by name ascending
        if len(consultants) >= 2:
            names = [c.get("full_name", "") for c in consultants]
            assert names == sorted(names), "Not sorted by name_asc"
            print(f"Sorted names (name_asc): {names[:5]}")
    
    def test_consultant_tracking_sort_by_message_change_desc(self, dealer_headers):
        """Test sort_by=message_change_desc"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=message_change_desc", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        consultants = data.get("consultants", [])
        if len(consultants) >= 2:
            changes = [c.get("message_change_7d", 0) for c in consultants]
            assert changes == sorted(changes, reverse=True), "Not sorted by message_change_desc"
            print(f"Sorted changes (message_change_desc): {changes[:5]}")
    
    def test_consultant_tracking_sort_by_messages_desc(self, dealer_headers):
        """Test sort_by=messages_desc"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=messages_desc", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        consultants = data.get("consultants", [])
        if len(consultants) >= 2:
            messages = [c.get("message_count", 0) for c in consultants]
            assert messages == sorted(messages, reverse=True), "Not sorted by messages_desc"
            print(f"Sorted messages (messages_desc): {messages[:5]}")
    
    def test_consultant_tracking_unauthorized(self):
        """Test without auth returns 401 or 403"""
        res = requests.get(f"{BASE_URL}/api/dealer/consultant-tracking")
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"


# =================== GET /api/dealer/favorites tests ===================

class TestDealerFavorites:
    """Favorites endpoint tests (regression)"""
    
    def test_favorites_returns_200(self, dealer_headers):
        """Test GET /api/dealer/favorites returns 200"""
        res = requests.get(f"{BASE_URL}/api/dealer/favorites", headers=dealer_headers)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    
    def test_favorites_has_three_lists(self, dealer_headers):
        """Test response has 3 lists + summary"""
        res = requests.get(f"{BASE_URL}/api/dealer/favorites", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        
        # 3 lists
        assert "favorite_listings" in data, "Missing 'favorite_listings'"
        assert "favorite_searches" in data, "Missing 'favorite_searches'"
        assert "favorite_sellers" in data, "Missing 'favorite_sellers'"
        assert isinstance(data["favorite_listings"], list)
        assert isinstance(data["favorite_searches"], list)
        assert isinstance(data["favorite_sellers"], list)
        
        # Summary with counts
        assert "summary" in data, "Missing 'summary'"
        summary = data["summary"]
        assert "favorite_listings_count" in summary
        assert "favorite_searches_count" in summary
        assert "favorite_sellers_count" in summary
        
        print(f"Favorites summary: {summary}")
    
    def test_favorites_unauthorized(self):
        """Test without auth returns 401 or 403"""
        res = requests.get(f"{BASE_URL}/api/dealer/favorites")
        assert res.status_code in [401, 403]


# =================== GET /api/dealer/reports tests ===================

class TestDealerReports:
    """Reports endpoint tests (regression)"""
    
    def test_reports_valid_windows(self, dealer_headers):
        """Test valid window_days values: 7, 14, 30, 90"""
        for days in [7, 14, 30, 90]:
            res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days={days}", headers=dealer_headers)
            assert res.status_code == 200, f"Expected 200 for window_days={days}, got {res.status_code}"
            data = res.json()
            assert "kpis" in data
            assert "filters" in data
            assert "report_sections" in data
            assert "package_reports" in data
            assert "doping_usage_report" in data
            print(f"Reports for {days} days: OK")
    
    def test_reports_invalid_window_31(self, dealer_headers):
        """Test invalid window_days=31 returns 400"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=31", headers=dealer_headers)
        assert res.status_code == 400, f"Expected 400 for window_days=31, got {res.status_code}"
        print("window_days=31 correctly rejected with 400")
    
    def test_reports_invalid_window_15(self, dealer_headers):
        """Test invalid window_days=15 returns 400"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=15", headers=dealer_headers)
        assert res.status_code == 400, f"Expected 400 for window_days=15, got {res.status_code}"
        print("window_days=15 correctly rejected with 400")
    
    def test_reports_kpis_structure(self, dealer_headers):
        """Test reports kpis structure"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=30", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        kpis = data.get("kpis", {})
        assert "views_7d" in kpis, "Missing views_7d in kpis"
        assert "contact_clicks_7d" in kpis, "Missing contact_clicks_7d in kpis"
        print(f"KPIs: views_7d={kpis['views_7d']}, contact_clicks_7d={kpis['contact_clicks_7d']}")
    
    def test_reports_sections_structure(self, dealer_headers):
        """Test report_sections structure"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=30", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        sections = data.get("report_sections", {})
        
        # Expected section keys
        expected_sections = [
            "listing_report", "views_report", "favorites_report",
            "messages_report", "mobile_calls_report"
        ]
        for section_key in expected_sections:
            assert section_key in sections, f"Missing '{section_key}' in report_sections"
            section = sections[section_key]
            # Each section should have these fields
            for field in ["title", "current_value", "previous_value", "change_pct", "total", "series"]:
                assert field in section, f"Missing '{field}' in {section_key}"
            print(f"Section {section_key}: current={section['current_value']}, change={section['change_pct']}%")
    
    def test_reports_package_structure(self, dealer_headers):
        """Test package_reports structure"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=30", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        pkg = data.get("package_reports", {})
        
        for field in ["package_name", "period", "used", "remaining", "quota_limit", "usage_rows"]:
            assert field in pkg, f"Missing '{field}' in package_reports"
        assert isinstance(pkg["usage_rows"], list)
        print(f"Package: used={pkg['used']}, remaining={pkg['remaining']}, limit={pkg['quota_limit']}")
    
    def test_reports_doping_structure(self, dealer_headers):
        """Test doping_usage_report structure"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports?window_days=30", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        doping = data.get("doping_usage_report", {})
        
        for field in ["total_used", "total_views", "series_used", "series_views"]:
            assert field in doping, f"Missing '{field}' in doping_usage_report"
        print(f"Doping: total_used={doping['total_used']}, total_views={doping['total_views']}")
    
    def test_reports_unauthorized(self):
        """Test without auth returns 401 or 403"""
        res = requests.get(f"{BASE_URL}/api/dealer/reports")
        assert res.status_code in [401, 403]


# =================== GET /api/dealer/messages tests (regression) ===================

class TestDealerMessages:
    """Messages endpoint tests (regression)"""
    
    def test_messages_returns_200(self, dealer_headers):
        """Test GET /api/dealer/messages returns 200"""
        res = requests.get(f"{BASE_URL}/api/dealer/messages", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        
        assert "items" in data
        assert "notification_items" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "listing_messages" in summary
        assert "notifications" in summary
        assert "unread_listing_messages" in summary
        
        print(f"Messages summary: {summary}")
    
    def test_messages_mark_read_invalid_uuid(self, dealer_headers):
        """Test mark-read with invalid UUID returns 400"""
        res = requests.post(
            f"{BASE_URL}/api/dealer/messages/invalid-uuid/read",
            headers=dealer_headers,
            json={}
        )
        assert res.status_code == 400, f"Expected 400, got {res.status_code}"
    
    def test_messages_mark_read_not_found(self, dealer_headers):
        """Test mark-read with non-existent conversation returns 404"""
        res = requests.post(
            f"{BASE_URL}/api/dealer/messages/00000000-0000-0000-0000-000000000000/read",
            headers=dealer_headers,
            json={}
        )
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"


# =================== GET /api/dealer/customers tests (regression) ===================

class TestDealerCustomers:
    """Customers endpoint tests (regression)"""
    
    def test_customers_returns_200(self, dealer_headers):
        """Test GET /api/dealer/customers returns 200"""
        res = requests.get(f"{BASE_URL}/api/dealer/customers", headers=dealer_headers)
        assert res.status_code == 200
        data = res.json()
        
        assert "items" in data
        assert "non_store_users" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "users_count" in summary
        assert "non_store_users_count" in summary
        
        print(f"Customers summary: {summary}")
    
    def test_customers_unauthorized(self):
        """Test without auth returns 401 or 403"""
        res = requests.get(f"{BASE_URL}/api/dealer/customers")
        assert res.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
