"""
P0 Toplu Kapanış - Corporate Dashboard Endpoint Tests
Tests: Summary, Listings, Messages, Customers, Favorites, Reports, Consultant Tracking
All endpoints tested for real data + empty-state handling (no mock fallbacks)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
DEALER_EMAIL = "dealer1772201722@example.com"
DEALER_PASSWORD = "Dealer123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        timeout=15
    )
    if response.status_code != 200:
        pytest.skip(f"Dealer login failed: {response.status_code} - {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


class TestDealerDashboardSummary:
    """GET /api/dealer/dashboard/summary - Module A: Summary endpoint tests"""

    def test_summary_returns_200(self, dealer_token):
        """Summary endpoint should return 200 with valid dealer token"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_summary_response_schema(self, dealer_token):
        """Summary should return proper schema with widgets and overview"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify top-level keys
        assert "widgets" in data, "Missing 'widgets' in response"
        assert "overview" in data, "Missing 'overview' in response"
        assert isinstance(data["widgets"], list), "widgets should be a list"
        
        # Verify overview structure
        overview = data["overview"]
        assert "store_performance" in overview, "Missing store_performance in overview"
        assert "package_summary" in overview, "Missing package_summary in overview"
        assert "kpi_cards" in overview, "Missing kpi_cards in overview"
        assert "data_notice" in overview, "Missing data_notice in overview"

    def test_summary_kpi_cards_structure(self, dealer_token):
        """Summary KPI cards should have proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        kpi_cards = response.json()["overview"]["kpi_cards"]
        
        # Verify KPI keys exist (values can be 0 for empty state)
        assert "published_listing_count" in kpi_cards
        assert "demand_customer_count" in kpi_cards
        assert "matching_listing_count" in kpi_cards
        
        # Values should be integers
        assert isinstance(kpi_cards["published_listing_count"], int)
        assert isinstance(kpi_cards["demand_customer_count"], int)
        assert isinstance(kpi_cards["matching_listing_count"], int)

    def test_summary_store_performance_structure(self, dealer_token):
        """Store performance section should have proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        store_perf = response.json()["overview"]["store_performance"]
        
        assert "visit_count_last_24h" in store_perf
        assert "visit_count_last_7d" in store_perf
        assert "visit_breakdown" in store_perf
        assert isinstance(store_perf["visit_breakdown"], list)

    def test_summary_package_summary_structure(self, dealer_token):
        """Package summary should have listing quota fields"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        pkg_summary = response.json()["overview"]["package_summary"]
        
        assert "listing_quota_used" in pkg_summary
        assert "listing_quota_remaining" in pkg_summary

    def test_summary_data_notice_empty_state(self, dealer_token):
        """Data notice should indicate if demand data is available"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data_notice = response.json()["overview"]["data_notice"]
        
        assert "demand_data_available" in data_notice
        assert isinstance(data_notice["demand_data_available"], bool)
        # If no demand data, message should explain
        if not data_notice["demand_data_available"]:
            assert "message" in data_notice

    def test_summary_requires_dealer_role(self, admin_token):
        """Summary endpoint should reject non-dealer users"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        # Admin should be denied (401 or 403)
        assert response.status_code in [401, 403], f"Expected 401/403 for admin, got {response.status_code}"


class TestDealerListings:
    """GET /api/dealer/listings - Module B: Listings endpoint tests"""

    def test_listings_returns_200(self, dealer_token):
        """Listings endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/listings?status=all",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_listings_response_schema(self, dealer_token):
        """Listings should return items array and quota object"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/listings?status=all",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "quota" in data, "Missing 'quota' in response"
        assert isinstance(data["items"], list)
        
        # Verify quota structure
        quota = data["quota"]
        assert "limit" in quota
        assert "used" in quota
        assert "remaining" in quota

    def test_listings_item_structure(self, dealer_token):
        """Each listing item should have proper fields"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/listings?status=all",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        items = response.json()["items"]
        
        # If items exist, check structure
        for item in items[:5]:  # Check first 5
            assert "id" in item
            assert "title" in item
            assert "status" in item

    def test_listings_status_filter_active(self, dealer_token):
        """Listings should filter by status=active"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/listings?status=active",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["status"] == "active"

    def test_listings_requires_auth(self):
        """Listings endpoint should require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/listings?status=all",
            timeout=15
        )
        assert response.status_code == 401


class TestDealerMessages:
    """GET /api/dealer/messages + POST /api/dealer/messages/{id}/read - Module C: Messages tests"""

    def test_messages_returns_200(self, dealer_token):
        """Messages endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_messages_response_schema(self, dealer_token):
        """Messages should return items, notification_items, and summary"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "notification_items" in data, "Missing 'notification_items' in response"
        assert "summary" in data, "Missing 'summary' in response"
        assert isinstance(data["items"], list)
        assert isinstance(data["notification_items"], list)

    def test_messages_summary_structure(self, dealer_token):
        """Messages summary should have proper counts"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/messages",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        summary = response.json()["summary"]
        
        assert "listing_messages" in summary
        assert "notifications" in summary
        assert "unread_listing_messages" in summary

    def test_mark_conversation_read_invalid_id(self, dealer_token):
        """Mark read should return 400 for invalid conversation_id"""
        response = requests.post(
            f"{BASE_URL}/api/dealer/messages/invalid-id/read",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 400

    def test_mark_conversation_read_not_found(self, dealer_token):
        """Mark read should return 404 for non-existent conversation"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/dealer/messages/{fake_uuid}/read",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 404


class TestDealerCustomers:
    """GET /api/dealer/customers - Module D: Customers endpoint tests"""

    def test_customers_returns_200(self, dealer_token):
        """Customers endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_customers_response_schema(self, dealer_token):
        """Customers should return items, non_store_users, and summary"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data, "Missing 'items' in response"
        assert "non_store_users" in data, "Missing 'non_store_users' in response"
        assert "summary" in data, "Missing 'summary' in response"
        assert isinstance(data["items"], list)
        assert isinstance(data["non_store_users"], list)

    def test_customers_summary_structure(self, dealer_token):
        """Customers summary should have user counts"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/customers",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        summary = response.json()["summary"]
        
        assert "users_count" in summary
        assert "non_store_users_count" in summary


class TestDealerFavorites:
    """GET /api/dealer/favorites - Module E: Favorites endpoint tests"""

    def test_favorites_returns_200(self, dealer_token):
        """Favorites endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_favorites_response_schema(self, dealer_token):
        """Favorites should return listings, searches, sellers, and summary"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "favorite_listings" in data, "Missing 'favorite_listings' in response"
        assert "favorite_searches" in data, "Missing 'favorite_searches' in response"
        assert "favorite_sellers" in data, "Missing 'favorite_sellers' in response"
        assert "summary" in data, "Missing 'summary' in response"
        
        assert isinstance(data["favorite_listings"], list)
        assert isinstance(data["favorite_searches"], list)
        assert isinstance(data["favorite_sellers"], list)

    def test_favorites_summary_structure(self, dealer_token):
        """Favorites summary should have counts for each section"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/favorites",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        summary = response.json()["summary"]
        
        assert "favorite_listings_count" in summary
        assert "favorite_searches_count" in summary
        assert "favorite_sellers_count" in summary


class TestDealerReports:
    """GET /api/dealer/reports - Module F: Reports endpoint tests"""

    def test_reports_returns_200_default_window(self, dealer_token):
        """Reports endpoint should return 200 with default window_days=30"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_reports_response_schema(self, dealer_token):
        """Reports should return kpis and report_sections"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "kpis" in data, "Missing 'kpis' in response"
        assert "report_sections" in data, "Missing 'report_sections' in response"

    def test_reports_kpis_structure(self, dealer_token):
        """Reports KPIs should have views_7d and contact_clicks_7d"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=30",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        kpis = response.json()["kpis"]
        
        assert "views_7d" in kpis
        assert "contact_clicks_7d" in kpis

    def test_reports_window_days_7(self, dealer_token):
        """Reports should accept window_days=7"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=7",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200

    def test_reports_window_days_14(self, dealer_token):
        """Reports should accept window_days=14"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=14",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200

    def test_reports_window_days_90(self, dealer_token):
        """Reports should accept window_days=90"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=90",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200

    def test_reports_invalid_window_days(self, dealer_token):
        """Reports should reject invalid window_days values"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/reports?window_days=15",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 400


class TestDealerConsultantTracking:
    """GET /api/dealer/consultant-tracking - Module G: Consultant Tracking tests"""

    def test_consultant_tracking_returns_200(self, dealer_token):
        """Consultant tracking endpoint should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=rating_desc",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_consultant_tracking_response_schema(self, dealer_token):
        """Consultant tracking should return consultants, evaluations, summary"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=rating_desc",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "consultants" in data, "Missing 'consultants' in response"
        assert "evaluations" in data, "Missing 'evaluations' in response"
        assert "summary" in data, "Missing 'summary' in response"
        
        assert isinstance(data["consultants"], list)
        assert isinstance(data["evaluations"], list)

    def test_consultant_tracking_summary_structure(self, dealer_token):
        """Consultant tracking summary should have counts"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=rating_desc",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200
        summary = response.json()["summary"]
        
        assert "consultants_count" in summary
        assert "evaluations_count" in summary

    def test_consultant_tracking_sort_by_name(self, dealer_token):
        """Consultant tracking should accept sort_by=name_asc"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=name_asc",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200

    def test_consultant_tracking_sort_by_message_change(self, dealer_token):
        """Consultant tracking should accept sort_by=message_change_desc"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=message_change_desc",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200

    def test_consultant_tracking_sort_by_messages(self, dealer_token):
        """Consultant tracking should accept sort_by=messages_desc"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/consultant-tracking?sort_by=messages_desc",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15
        )
        assert response.status_code == 200


class TestDealerEndpointsAuthorization:
    """Authorization tests for all dealer endpoints"""

    def test_all_endpoints_require_auth(self):
        """All dealer endpoints should require authentication"""
        endpoints = [
            "/api/dealer/dashboard/summary",
            "/api/dealer/listings?status=all",
            "/api/dealer/messages",
            "/api/dealer/customers",
            "/api/dealer/favorites",
            "/api/dealer/reports?window_days=30",
            "/api/dealer/consultant-tracking?sort_by=rating_desc",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            assert response.status_code == 401, f"{endpoint} should require auth, got {response.status_code}"

    def test_admin_cannot_access_dealer_endpoints(self, admin_token):
        """Admin role should not access dealer-only endpoints"""
        endpoints = [
            "/api/dealer/dashboard/summary",
            "/api/dealer/listings?status=all",
            "/api/dealer/messages",
            "/api/dealer/customers",
            "/api/dealer/favorites",
            "/api/dealer/reports?window_days=30",
            "/api/dealer/consultant-tracking?sort_by=rating_desc",
        ]
        
        for endpoint in endpoints:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10
            )
            assert response.status_code in [401, 403], \
                f"Admin should not access {endpoint}, got {response.status_code}"
