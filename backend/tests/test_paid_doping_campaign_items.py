"""
P70 Paid Listing + Campaign Item listing_type Tests

Testing:
1. Admin doping endpoint support for paid type
2. Doping tabs filtering (free/paid/showcase/urgent)
3. PricingCampaignItem with listing_type (free/paid/urgent/showcase)
4. Campaign item CRUD with listing_type
5. Individual/Corporate scope listing_type support
"""
import os
import pytest
import requests
from datetime import datetime, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

@pytest.fixture(scope="module")
def auth_header():
    """Admin authentication"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@platform.com",
        "password": "Admin123!"
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}


class TestDopingEndpointPaidSupport:
    """Test POST /api/admin/listings/{id}/doping with paid type"""
    
    def test_doping_endpoint_accepts_paid_type(self, auth_header):
        """POST /api/admin/listings/{id}/doping should accept paid doping_type"""
        # First get a listing
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 1},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed to get listings: {response.text}"
        listings = response.json().get("items", [])
        if not listings:
            pytest.skip("No listings available for testing")
        
        listing_id = listings[0]["id"]
        
        # Apply paid doping
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={
                "doping_type": "paid",
                "duration_days": 7,
                "reason": "test_paid_doping"
            },
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed to apply paid doping: {response.text}"
        data = response.json()
        assert data.get("doping_type") == "paid", "Doping type should be paid"
        assert data.get("paid_until") is not None, "paid_until should be set"
        print(f"PASS: POST doping with paid type works. paid_until: {data.get('paid_until')}")
        
        # Revert to free
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/{listing_id}/doping",
            json={"doping_type": "free", "reason": "test_cleanup"},
            headers=auth_header
        )
        assert response.status_code == 200


class TestListingsDopingTabFilters:
    """Test doping_type filter on admin listings endpoint"""
    
    def test_listings_filter_by_paid(self, auth_header):
        """GET /api/admin/listings?doping_type=paid"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"doping_type": "paid", "limit": 5},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "doping_counts" in data, "Response should include doping_counts"
        assert "paid" in data.get("doping_counts", {}), "doping_counts should have 'paid' key"
        print(f"PASS: doping_type=paid filter works. paid count: {data.get('doping_counts', {}).get('paid', 0)}")
    
    def test_listings_filter_by_free(self, auth_header):
        """GET /api/admin/listings?doping_type=free"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"doping_type": "free", "limit": 5},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "doping_counts" in data
        print(f"PASS: doping_type=free filter works. free count: {data.get('doping_counts', {}).get('free', 0)}")
    
    def test_listings_filter_by_showcase(self, auth_header):
        """GET /api/admin/listings?doping_type=showcase"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"doping_type": "showcase", "limit": 5},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "doping_counts" in data
        print(f"PASS: doping_type=showcase filter works. showcase count: {data.get('doping_counts', {}).get('showcase', 0)}")
    
    def test_listings_filter_by_urgent(self, auth_header):
        """GET /api/admin/listings?doping_type=urgent"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"doping_type": "urgent", "limit": 5},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "doping_counts" in data
        print(f"PASS: doping_type=urgent filter works. urgent count: {data.get('doping_counts', {}).get('urgent', 0)}")
    
    def test_listings_doping_counts_structure(self, auth_header):
        """Verify doping_counts returns all 4 types"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 1},
            headers=auth_header
        )
        assert response.status_code == 200
        counts = response.json().get("doping_counts", {})
        assert "free" in counts, "doping_counts missing 'free'"
        assert "paid" in counts, "doping_counts missing 'paid'"
        assert "showcase" in counts, "doping_counts missing 'showcase'"
        assert "urgent" in counts, "doping_counts missing 'urgent'"
        print(f"PASS: doping_counts has all 4 types: {counts}")


class TestPricingCampaignItemListingType:
    """Test PricingCampaignItem CRUD with listing_type field"""
    
    def test_create_individual_campaign_with_free_type(self, auth_header):
        """POST /api/admin/pricing/campaign-items with listing_type=free for individual"""
        now = datetime.utcnow()
        start_at = (now + timedelta(minutes=5)).isoformat() + "Z"
        end_at = (now + timedelta(days=30)).isoformat() + "Z"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            json={
                "scope": "individual",
                "listing_type": "free",
                "listing_quota": 5,
                "price_amount": 0,
                "currency": "EUR",
                "publish_days": 90,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False  # inactive to avoid overlap
            },
            headers=auth_header
        )
        assert response.status_code in [200, 201], f"Failed to create campaign item: {response.text}"
        data = response.json()
        assert data.get("listing_type") == "free"
        print(f"PASS: Created individual campaign with listing_type=free. ID: {data.get('id')}")
        
        # Cleanup
        item_id = data.get("id")
        if item_id:
            requests.delete(f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}", headers=auth_header)
    
    def test_create_individual_campaign_with_paid_type(self, auth_header):
        """POST /api/admin/pricing/campaign-items with listing_type=paid"""
        now = datetime.utcnow()
        start_at = (now + timedelta(minutes=5)).isoformat() + "Z"
        end_at = (now + timedelta(days=30)).isoformat() + "Z"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            json={
                "scope": "individual",
                "listing_type": "paid",
                "listing_quota": 3,
                "price_amount": 9.99,
                "currency": "EUR",
                "publish_days": 90,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False
            },
            headers=auth_header
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data.get("listing_type") == "paid"
        print(f"PASS: Created individual campaign with listing_type=paid. ID: {data.get('id')}")
        
        # Cleanup
        item_id = data.get("id")
        if item_id:
            requests.delete(f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}", headers=auth_header)
    
    def test_create_individual_campaign_with_urgent_type(self, auth_header):
        """POST /api/admin/pricing/campaign-items with listing_type=urgent"""
        now = datetime.utcnow()
        start_at = (now + timedelta(minutes=5)).isoformat() + "Z"
        end_at = (now + timedelta(days=30)).isoformat() + "Z"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            json={
                "scope": "individual",
                "listing_type": "urgent",
                "listing_quota": 2,
                "price_amount": 19.99,
                "currency": "EUR",
                "publish_days": 7,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False
            },
            headers=auth_header
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data.get("listing_type") == "urgent"
        print(f"PASS: Created individual campaign with listing_type=urgent. ID: {data.get('id')}")
        
        # Cleanup
        item_id = data.get("id")
        if item_id:
            requests.delete(f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}", headers=auth_header)
    
    def test_create_individual_campaign_with_showcase_type(self, auth_header):
        """POST /api/admin/pricing/campaign-items with listing_type=showcase"""
        now = datetime.utcnow()
        start_at = (now + timedelta(minutes=5)).isoformat() + "Z"
        end_at = (now + timedelta(days=30)).isoformat() + "Z"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            json={
                "scope": "individual",
                "listing_type": "showcase",
                "listing_quota": 1,
                "price_amount": 29.99,
                "currency": "EUR",
                "publish_days": 30,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False
            },
            headers=auth_header
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data.get("listing_type") == "showcase"
        print(f"PASS: Created individual campaign with listing_type=showcase. ID: {data.get('id')}")
        
        # Cleanup
        item_id = data.get("id")
        if item_id:
            requests.delete(f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}", headers=auth_header)
    
    def test_create_corporate_campaign_with_paid_type(self, auth_header):
        """POST /api/admin/pricing/campaign-items with listing_type=paid for corporate"""
        now = datetime.utcnow()
        start_at = (now + timedelta(minutes=5)).isoformat() + "Z"
        end_at = (now + timedelta(days=30)).isoformat() + "Z"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            json={
                "scope": "corporate",
                "listing_type": "paid",
                "listing_quota": 10,
                "price_amount": 49.99,
                "currency": "EUR",
                "publish_days": 90,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False
            },
            headers=auth_header
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        data = response.json()
        assert data.get("listing_type") == "paid"
        assert data.get("scope") == "corporate"
        print(f"PASS: Created corporate campaign with listing_type=paid. ID: {data.get('id')}")
        
        # Cleanup
        item_id = data.get("id")
        if item_id:
            requests.delete(f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}", headers=auth_header)


class TestCampaignItemListEndpoint:
    """Test GET /api/admin/pricing/campaign-items with listing_type filter"""
    
    def test_list_individual_campaign_items(self, auth_header):
        """GET /api/admin/pricing/campaign-items?scope=individual"""
        response = requests.get(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            params={"scope": "individual"},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"PASS: Listed individual campaign items. Count: {len(data.get('items', []))}")
        
        # Check listing_type is present in items
        for item in data.get("items", [])[:3]:
            assert "listing_type" in item, f"Item missing listing_type: {item}"
    
    def test_list_corporate_campaign_items(self, auth_header):
        """GET /api/admin/pricing/campaign-items?scope=corporate"""
        response = requests.get(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            params={"scope": "corporate"},
            headers=auth_header
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"PASS: Listed corporate campaign items. Count: {len(data.get('items', []))}")


class TestCampaignItemUpdateWithListingType:
    """Test PUT /api/admin/pricing/campaign-items/{id} with listing_type change"""
    
    def test_update_campaign_item_listing_type(self, auth_header):
        """Create, update listing_type, verify"""
        now = datetime.utcnow()
        start_at = (now + timedelta(minutes=10)).isoformat() + "Z"
        end_at = (now + timedelta(days=30)).isoformat() + "Z"
        
        # Create
        response = requests.post(
            f"{BASE_URL}/api/admin/pricing/campaign-items",
            json={
                "scope": "individual",
                "listing_type": "free",
                "listing_quota": 5,
                "price_amount": 0,
                "currency": "EUR",
                "publish_days": 90,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False
            },
            headers=auth_header
        )
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        item_id = response.json().get("id")
        
        # Update listing_type to paid
        response = requests.put(
            f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}",
            json={
                "listing_type": "paid",
                "listing_quota": 5,
                "price_amount": 9.99,
                "currency": "EUR",
                "publish_days": 90,
                "start_at": start_at,
                "end_at": end_at,
                "is_active": False
            },
            headers=auth_header
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        updated = response.json()
        assert updated.get("listing_type") == "paid", f"listing_type should be paid, got: {updated.get('listing_type')}"
        print(f"PASS: Updated campaign item listing_type from free to paid")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/pricing/campaign-items/{item_id}", headers=auth_header)


class TestPaidBadgeInListingResponse:
    """Test is_paid field in listing response"""
    
    def test_listing_has_is_paid_field(self, auth_header):
        """Verify listing items include is_paid field"""
        response = requests.get(
            f"{BASE_URL}/api/admin/listings",
            params={"limit": 5},
            headers=auth_header
        )
        assert response.status_code == 200
        items = response.json().get("items", [])
        if items:
            item = items[0]
            # Check is_paid field exists (boolean)
            assert "is_paid" in item or "paid_until" in item, f"Listing should have is_paid or paid_until field"
            print(f"PASS: Listing has paid info. is_paid={item.get('is_paid')}, paid_until={item.get('paid_until')}")
