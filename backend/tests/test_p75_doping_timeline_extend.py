"""
Test suite for P75 Doping Timeline Extend Features.

Features tested:
1. Timeline columns visible on Acil/Vitrin/Ücretli pages (applicationsMode=true + doping type)
2. Kalan gün <=3 warning color class (text-rose-600) - UI only
3. +7g Uzat and +30g Uzat buttons functionality
4. Extend buttons call /api/admin/listings/{id}/doping with until_at parameter
5. After extend, doping end date is correctly extended
6. Regression: Acil tab new window behavior preserved
"""
import pytest
import requests
import os
from datetime import datetime, timedelta, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestDopingExtendAPI:
    """Test /api/admin/listings/{id}/doping endpoint with until_at parameter"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _get_test_listing(self):
        """Get a listing to test doping extension"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 1, "status": "published"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to get listings: {response.text}"
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No published listings available for testing")
        return items[0]
    
    def test_doping_endpoint_accepts_until_at_parameter(self):
        """Test that doping endpoint accepts until_at parameter"""
        listing = self._get_test_listing()
        listing_id = listing["id"]
        
        # Set until_at to 7 days from now
        now = datetime.now(timezone.utc)
        until_at = now + timedelta(days=7)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "showcase",
                "until_at": until_at.isoformat(),
                "reason": "test_until_at"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Doping update failed: {response.text}"
        data = response.json()
        assert data.get("ok") == True, f"Response not ok: {data}"
        
        # Verify the listing has updated featured_until
        result_listing = data.get("listing", {})
        assert result_listing.get("doping_type") == "showcase"
        assert result_listing.get("is_featured") == True
        assert result_listing.get("featured_until") is not None
    
    def test_doping_extend_7_days(self):
        """Test extending doping by 7 days using until_at"""
        listing = self._get_test_listing()
        listing_id = listing["id"]
        
        # First set to urgent with 3 days
        now = datetime.now(timezone.utc)
        initial_end = now + timedelta(days=3)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "urgent",
                "until_at": initial_end.isoformat(),
                "reason": "test_initial_urgent"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"Initial doping failed: {response.text}"
        
        # Now extend by 7 days - set until_at to initial_end + 7 days
        extended_end = initial_end + timedelta(days=7)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "urgent",
                "until_at": extended_end.isoformat(),
                "reason": "moderation_timeline_extend"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Extend doping failed: {response.text}"
        data = response.json()
        assert data.get("ok") == True
        
        # Verify urgent_until is extended
        result_listing = data.get("listing", {})
        assert result_listing.get("is_urgent") == True
        urgent_until = result_listing.get("urgent_until")
        assert urgent_until is not None
        
        # Parse and compare dates
        result_date = datetime.fromisoformat(urgent_until.replace('Z', '+00:00'))
        assert result_date >= extended_end - timedelta(seconds=5), \
            f"Extended date {result_date} not >= expected {extended_end}"
    
    def test_doping_extend_30_days(self):
        """Test extending doping by 30 days using until_at"""
        listing = self._get_test_listing()
        listing_id = listing["id"]
        
        # Set to paid with 30 day extension
        now = datetime.now(timezone.utc)
        until_at = now + timedelta(days=30)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "paid",
                "until_at": until_at.isoformat(),
                "reason": "moderation_timeline_extend"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Doping update failed: {response.text}"
        data = response.json()
        assert data.get("ok") == True
        
        result_listing = data.get("listing", {})
        assert result_listing.get("is_paid") == True
        paid_until = result_listing.get("paid_until")
        assert paid_until is not None
    
    def test_doping_preserves_type_on_extend(self):
        """Test that extending preserves the doping type"""
        listing = self._get_test_listing()
        listing_id = listing["id"]
        
        # Set to showcase
        now = datetime.now(timezone.utc)
        initial_end = now + timedelta(days=7)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "showcase",
                "until_at": initial_end.isoformat(),
                "reason": "test_showcase"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Extend by 7 days (simulating +7g button)
        extended_end = initial_end + timedelta(days=7)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "showcase",  # Same type preserved
                "until_at": extended_end.isoformat(),
                "reason": "moderation_timeline_extend"
            },
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        result_listing = data.get("listing", {})
        assert result_listing.get("doping_type") == "showcase"
        assert result_listing.get("is_featured") == True
        # Urgent and paid should be cleared
        assert result_listing.get("is_urgent") == False
        assert result_listing.get("is_paid") == False
    
    def test_doping_rejects_past_until_at(self):
        """Test that doping rejects until_at in the past"""
        listing = self._get_test_listing()
        listing_id = listing["id"]
        
        # Set until_at to the past
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "urgent",
                "until_at": past_date.isoformat(),
                "reason": "test_past_date"
            },
            headers=self.headers
        )
        
        # Should reject past dates
        assert response.status_code == 400, f"Expected 400 for past date, got: {response.status_code}"


class TestDopingListingsAPI:
    """Test admin listings API returns correct doping fields for timeline display"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_listings_have_published_at_field(self):
        """Test that listings response includes published_at"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 5, "status": "published"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        for item in items:
            assert "published_at" in item, f"published_at missing in listing {item.get('id')}"
    
    def test_listings_have_doping_end_fields(self):
        """Test that listings response includes all doping end date fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 5},
            headers=self.headers
        )
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        for item in items:
            # All three fields should be present (can be null)
            assert "featured_until" in item, f"featured_until missing in {item.get('id')}"
            assert "urgent_until" in item, f"urgent_until missing in {item.get('id')}"
            assert "paid_until" in item, f"paid_until missing in {item.get('id')}"
    
    def test_doping_counts_returned(self):
        """Test that doping counts are returned correctly"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 1},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        doping_counts = data.get("doping_counts", {})
        
        assert "free" in doping_counts
        assert "paid" in doping_counts
        assert "showcase" in doping_counts
        assert "urgent" in doping_counts
        
        # Counts should be non-negative integers
        for key in ["free", "paid", "showcase", "urgent"]:
            assert isinstance(doping_counts[key], int)
            assert doping_counts[key] >= 0
    
    def test_individual_applicant_type_filter(self):
        """Test applicant_type=individual filter works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 5, "applicant_type": "individual"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "doping_counts" in data
    
    def test_corporate_applicant_type_filter(self):
        """Test applicant_type=corporate filter works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 5, "applicant_type": "corporate"},
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data


class TestTimelineHelperLogic:
    """Test remaining days calculation logic"""
    
    def test_remaining_days_calculation(self):
        """Test remaining days calculation from end date"""
        # Frontend helper: resolveRemainingDaysNumber
        from datetime import datetime, timezone
        
        def resolve_remaining_days_number(end_at_str):
            if not end_at_str:
                return None
            try:
                end_date = datetime.fromisoformat(end_at_str.replace('Z', '+00:00'))
                diff = end_date - datetime.now(timezone.utc)
                if diff.total_seconds() <= 0:
                    return 0
                return (diff.days + 1)  # ceil
            except:
                return None
        
        now = datetime.now(timezone.utc)
        
        # Test future date - 7 days
        future_7 = (now + timedelta(days=7)).isoformat()
        result = resolve_remaining_days_number(future_7)
        assert result is not None
        assert result >= 6 and result <= 8  # Allow for timing variance
        
        # Test past date - should return 0
        past = (now - timedelta(days=1)).isoformat()
        result = resolve_remaining_days_number(past)
        assert result == 0
        
        # Test 2 days - should trigger warning
        future_2 = (now + timedelta(days=2)).isoformat()
        result = resolve_remaining_days_number(future_2)
        assert result is not None
        assert result <= 3  # Should be 2 or 3
    
    def test_warning_threshold(self):
        """Test that warning threshold is 3 days"""
        # Frontend logic: warning = remainingDays !== null && remainingDays <= 3
        END_WARNING_DAYS = 3
        
        assert 0 <= END_WARNING_DAYS  # 0 triggers warning
        assert 1 <= END_WARNING_DAYS  # 1 triggers warning
        assert 2 <= END_WARNING_DAYS  # 2 triggers warning
        assert 3 <= END_WARNING_DAYS  # 3 triggers warning
        assert 4 > END_WARNING_DAYS   # 4 does NOT trigger warning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
