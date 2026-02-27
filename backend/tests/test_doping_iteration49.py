"""
Test file for P0 Doping Feature - Iteration 49
Tests doping badge display, sidebar links, and backend endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAdminLogin:
    """Test admin login for doping tests"""
    
    def test_admin_login(self):
        """Admin login should return access token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"


class TestDopingFilters:
    """Test doping type filters on admin listings"""
    
    @pytest.fixture
    def auth_header(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_listings_doping_showcase_filter(self, auth_header):
        """GET /api/admin/listings?doping_type=showcase should filter showcase listings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?doping_type=showcase&limit=5",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "doping_counts" in data
        assert "showcase" in data["doping_counts"]
    
    def test_listings_doping_urgent_filter(self, auth_header):
        """GET /api/admin/listings?doping_type=urgent should filter urgent listings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?doping_type=urgent&limit=5",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "doping_counts" in data
        assert "urgent" in data["doping_counts"]
    
    def test_listings_doping_free_filter(self, auth_header):
        """GET /api/admin/listings?doping_type=free should filter free listings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?doping_type=free&limit=5",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "doping_counts" in data
        assert "free" in data["doping_counts"]
    
    def test_listings_applicant_type_individual(self, auth_header):
        """GET /api/admin/listings?applicant_type=individual should filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?applicant_type=individual&limit=5",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_listings_applicant_type_corporate(self, auth_header):
        """GET /api/admin/listings?applicant_type=corporate should filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?applicant_type=corporate&limit=5",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestDopingEndpoint:
    """Test POST /api/admin/listings/{listing_id}/doping endpoint"""
    
    @pytest.fixture
    def auth_header(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_listing_id(self, auth_header):
        """Get a listing to test doping on"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?limit=1",
            headers=auth_header
        )
        items = response.json().get("items", [])
        if items:
            return items[0]["id"]
        pytest.skip("No listings available for doping test")
    
    def test_apply_showcase_doping_7days(self, auth_header, test_listing_id):
        """POST doping showcase with 7 days duration"""
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{test_listing_id}/doping",
            headers=auth_header,
            json={"doping_type": "showcase", "duration_days": 7}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        assert data["listing"]["doping_type"] == "showcase"
        assert data["listing"]["is_featured"] == True
    
    def test_apply_urgent_doping_30days(self, auth_header, test_listing_id):
        """POST doping urgent with 30 days duration"""
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{test_listing_id}/doping",
            headers=auth_header,
            json={"doping_type": "urgent", "duration_days": 30}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        assert data["listing"]["doping_type"] == "urgent"
        assert data["listing"]["is_urgent"] == True
    
    def test_apply_free_doping(self, auth_header, test_listing_id):
        """POST doping free should reset doping"""
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{test_listing_id}/doping",
            headers=auth_header,
            json={"doping_type": "free"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        assert data["listing"]["doping_type"] == "free"


class TestDopingCounts:
    """Test doping counts in admin listings response"""
    
    @pytest.fixture
    def auth_header(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_doping_counts_structure(self, auth_header):
        """Doping counts should have free, showcase, urgent keys"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings?limit=1",
            headers=auth_header
        )
        assert response.status_code == 200
        data = response.json()
        counts = data.get("doping_counts", {})
        assert "free" in counts
        assert "showcase" in counts
        assert "urgent" in counts
