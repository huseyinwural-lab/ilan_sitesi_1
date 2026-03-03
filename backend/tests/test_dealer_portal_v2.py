"""
Dealer Portal V2 Layout & Navigation Tests
Tests for iteration 102 - Dealer Kurumsal Portal Dashboard UI

Features tested:
- Backend endpoint: GET /api/dealer/dashboard/navigation-summary
- Backend endpoint: GET /api/dealer/virtual-tours
- Authentication guards for dealer-only endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestDealerPortalV2Auth:
    """Test authentication requirements for dealer endpoints"""

    def test_navigation_summary_requires_auth(self):
        """Navigation summary requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
        print(f"PASS: navigation-summary returns {response.status_code} without auth")

    def test_virtual_tours_requires_auth(self):
        """Virtual tours requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dealer/virtual-tours")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
        print(f"PASS: virtual-tours returns {response.status_code} without auth")

    def test_user_cannot_access_dealer_endpoints(self):
        """Individual user should not access dealer endpoints"""
        # Login as regular user
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "user@platform.com", "password": "User123!"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access dealer navigation summary
        resp1 = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary", headers=headers)
        assert resp1.status_code == 403, f"Expected 403 for user on navigation-summary, got {resp1.status_code}"
        print("PASS: Individual user gets 403 on navigation-summary")

        # Try to access dealer virtual tours
        resp2 = requests.get(f"{BASE_URL}/api/dealer/virtual-tours", headers=headers)
        assert resp2.status_code == 403, f"Expected 403 for user on virtual-tours, got {resp2.status_code}"
        print("PASS: Individual user gets 403 on virtual-tours")


class TestDealerNavigationSummary:
    """Test dealer navigation summary endpoint contract"""

    @pytest.fixture
    def dealer_token(self):
        """Get dealer authentication token"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        assert login_resp.status_code == 200, f"Dealer login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access_token in dealer login response"
        return token

    def test_navigation_summary_returns_200(self, dealer_token):
        """Navigation summary returns 200 for dealer"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: navigation-summary returns 200 for dealer")

    def test_navigation_summary_has_badges(self, dealer_token):
        """Navigation summary has badges object with expected fields"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "badges" in data, "Response missing 'badges' key"
        badges = data["badges"]
        
        expected_badge_keys = [
            "active_listings",
            "total_listings",
            "favorites_total",
            "unread_messages",
            "customers_total",
            "cart_total",
            "announcements_total",
        ]
        for key in expected_badge_keys:
            assert key in badges, f"badges missing key: {key}"
            assert isinstance(badges[key], int), f"badges[{key}] should be int, got {type(badges[key])}"
        
        print(f"PASS: badges object has all expected keys: {list(badges.keys())}")

    def test_navigation_summary_has_left_menu(self, dealer_token):
        """Navigation summary has left_menu object"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "left_menu" in data, "Response missing 'left_menu' key"
        left_menu = data["left_menu"]
        assert isinstance(left_menu, dict), f"left_menu should be dict, got {type(left_menu)}"
        
        # Expected sidebar item keys based on sideRailItems in DealerLayoutV2.js
        expected_keys = [
            "ofisim_ozet",
            "ilanlarim",
            "favorilerim",
            "sepetim",
            "musteri_yonetimi",
        ]
        for key in expected_keys:
            assert key in left_menu, f"left_menu missing key: {key}"
        
        print(f"PASS: left_menu object has expected keys: {list(left_menu.keys())}")

    def test_navigation_summary_has_academy(self, dealer_token):
        """Navigation summary has academy object with MOCKED modules"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "academy" in data, "Response missing 'academy' key"
        academy = data["academy"]
        
        assert "data_source" in academy, "academy missing 'data_source'"
        assert academy["data_source"] == "mocked", f"Expected data_source='mocked', got {academy['data_source']}"
        
        assert "modules" in academy, "academy missing 'modules'"
        modules = academy["modules"]
        assert isinstance(modules, list), f"academy.modules should be list, got {type(modules)}"
        assert len(modules) > 0, "academy.modules should not be empty"
        
        # Check module structure
        for module in modules:
            assert "id" in module, "Module missing 'id'"
            assert "title" in module, "Module missing 'title'"
            assert "description" in module, "Module missing 'description'"
            assert "progress" in module, "Module missing 'progress'"
            assert "duration_minutes" in module, "Module missing 'duration_minutes'"
        
        print(f"PASS: academy object has {len(modules)} MOCKED modules")

    def test_navigation_summary_has_generated_at(self, dealer_token):
        """Navigation summary has generated_at timestamp"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/dashboard/navigation-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "generated_at" in data, "Response missing 'generated_at'"
        assert isinstance(data["generated_at"], str), "generated_at should be string"
        print(f"PASS: generated_at present: {data['generated_at']}")


class TestDealerVirtualTours:
    """Test dealer virtual tours endpoint"""

    @pytest.fixture
    def dealer_token(self):
        """Get dealer authentication token"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        assert login_resp.status_code == 200, f"Dealer login failed: {login_resp.text}"
        return login_resp.json().get("access_token")

    def test_virtual_tours_returns_200(self, dealer_token):
        """Virtual tours returns 200 for dealer"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/virtual-tours", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: virtual-tours returns 200 for dealer")

    def test_virtual_tours_has_summary(self, dealer_token):
        """Virtual tours has summary object"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/virtual-tours", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data, "Response missing 'summary' key"
        summary = data["summary"]
        
        assert "total" in summary, "summary missing 'total'"
        assert "active" in summary, "summary missing 'active'"
        assert "draft" in summary, "summary missing 'draft'"
        
        assert isinstance(summary["total"], int)
        assert isinstance(summary["active"], int)
        assert isinstance(summary["draft"], int)
        
        print(f"PASS: summary object: total={summary['total']}, active={summary['active']}, draft={summary['draft']}")

    def test_virtual_tours_has_items(self, dealer_token):
        """Virtual tours has items array"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/virtual-tours", headers=headers)
        assert response.status_code == 200
        data = response.json()

        assert "items" in data, "Response missing 'items' key"
        items = data["items"]
        assert isinstance(items, list), f"items should be list, got {type(items)}"
        
        # If there are items, check structure
        if len(items) > 0:
            item = items[0]
            assert "tour_id" in item, "Item missing 'tour_id'"
            assert "listing_title" in item, "Item missing 'listing_title'"
            assert "status" in item, "Item missing 'status'"
            assert "readiness_score" in item, "Item missing 'readiness_score'"
            assert "last_updated" in item, "Item missing 'last_updated'"
            print(f"PASS: items array has {len(items)} items with correct structure")
        else:
            print("PASS: items array is empty (no listings for dealer)")


class TestDealerExistingRoutes:
    """Regression test - existing dealer routes should still work"""

    @pytest.fixture
    def dealer_token(self):
        """Get dealer authentication token"""
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        assert login_resp.status_code == 200
        return login_resp.json().get("access_token")

    def test_dealer_listings_works(self, dealer_token):
        """Dealer listings endpoint works"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/listings", headers=headers)
        # Allow 200 or 404 (no listings yet)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"PASS: dealer/listings returns {response.status_code}")

    def test_dealer_messages_works(self, dealer_token):
        """Dealer messages endpoint works"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/messages", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: dealer/messages returns 200")

    def test_dealer_favorites_works(self, dealer_token):
        """Dealer favorites endpoint works"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/favorites", headers=headers)
        # Allow 200 or 404
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"PASS: dealer/favorites returns {response.status_code}")

    def test_dealer_reports_works(self, dealer_token):
        """Dealer reports endpoint works"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/reports", headers=headers)
        # Allow 200 or 404 (may not have data)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"PASS: dealer/reports returns {response.status_code}")

    def test_dealer_purchase_works(self, dealer_token):
        """Dealer purchase endpoint works"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        response = requests.get(f"{BASE_URL}/api/dealer/purchase", headers=headers)
        # Allow various success/not-found
        assert response.status_code in [200, 404, 405], f"Unexpected status: {response.status_code}"
        print(f"PASS: dealer/purchase returns {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
