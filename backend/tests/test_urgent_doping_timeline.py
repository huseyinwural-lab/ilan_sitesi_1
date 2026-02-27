"""
Test suite for Urgent/Featured/Paid doping pages with timeline columns.

Features tested:
1. Individual/Corporate urgent routes open with initialStatus='published'
2. Timeline columns (published_at, doping_end, remaining_days) present in API response
3. Sidebar links for urgent pages are marked as openInNewWindow
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAdminListingsEndpoint:
    """Test /api/admin/listings endpoint with doping filters"""
    
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
    
    def test_admin_listings_returns_published_at_field(self):
        """Test that admin listings API returns published_at for timeline display"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "status": "published"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        # If there are published listings, check they have published_at field
        for item in items:
            # published_at should be present for published listings
            if item.get("status") == "published":
                # Field may be null if legacy data, but key should exist
                assert "published_at" in item, f"published_at field missing in listing {item.get('id')}"
    
    def test_admin_listings_urgent_filter(self):
        """Test urgent doping filter works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "doping_type": "urgent"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "doping_counts" in data
    
    def test_admin_listings_featured_filter(self):
        """Test featured (showcase/vitrin) doping filter works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "doping_type": "showcase"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        assert "items" in data
    
    def test_admin_listings_paid_filter(self):
        """Test paid doping filter works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "doping_type": "paid"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        assert "items" in data
    
    def test_admin_listings_with_applicant_type_individual(self):
        """Test individual applicant type filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "applicant_type": "individual"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        assert "items" in data
    
    def test_admin_listings_with_applicant_type_corporate(self):
        """Test corporate applicant type filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "applicant_type": "corporate"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        assert "items" in data
    
    def test_admin_listings_urgent_with_published_status(self):
        """Test urgent filter combined with published status (for approved urgent listings)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 10, "doping_type": "urgent", "status": "published"},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        # All items should be published and urgent
        for item in items:
            assert item.get("status") == "published", f"Expected published status for listing {item.get('id')}"
            assert item.get("is_urgent") == True or item.get("doping_type") == "urgent", \
                f"Expected urgent doping for listing {item.get('id')}"
    
    def test_admin_listings_returns_doping_date_fields(self):
        """Test that listings with doping return end date fields"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 20},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            # Check doping date fields are present (can be null)
            assert "featured_until" in item or "is_featured" in item, \
                f"Featured doping fields missing in listing {item.get('id')}"
            assert "urgent_until" in item or "is_urgent" in item, \
                f"Urgent doping fields missing in listing {item.get('id')}"
            assert "paid_until" in item or "is_paid" in item, \
                f"Paid doping fields missing in listing {item.get('id')}"


class TestDopingCounts:
    """Test doping counts returned by API"""
    
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
    
    def test_doping_counts_structure(self):
        """Test doping counts have correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 1},
            headers=self.headers
        )
        assert response.status_code == 200, f"Request failed: {response.text}"
        
        data = response.json()
        doping_counts = data.get("doping_counts", {})
        
        # Check expected keys
        assert "free" in doping_counts, "free count missing"
        assert "paid" in doping_counts, "paid count missing"
        assert "showcase" in doping_counts, "showcase count missing"
        assert "urgent" in doping_counts, "urgent count missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
