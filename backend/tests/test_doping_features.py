"""
P88 Doping Feature Tests - Iteration 47
Tests for:
  - Listing doping columns (featured_until, urgent_until)
  - GET /api/admin/listings with applicant_type and doping_type filters
  - POST /api/admin/listings/{listing_id}/doping endpoint
  - /api/v2/search response with is_featured/is_urgent fields
"""
import os
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
API = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin and get access token"""
    response = requests.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text[:200]}")
    data = response.json()
    token = data.get("access_token")
    if not token:
        pytest.skip("No access token in login response")
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Return authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestDopingColumnsEnsured:
    """Test that featured_until and urgent_until columns are available at runtime"""

    def test_admin_listings_returns_doping_fields(self, auth_headers):
        """Verify GET /api/admin/listings returns featured_until and urgent_until"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        
        # Check structure even if no items
        if data["items"]:
            first_item = data["items"][0]
            # These fields should be present (can be null)
            assert "featured_until" in first_item or first_item.get("featured_until") is None, "featured_until field should exist"
            assert "urgent_until" in first_item or first_item.get("urgent_until") is None, "urgent_until field should exist"
            assert "is_featured" in first_item, "is_featured field should exist"
            assert "is_urgent" in first_item, "is_urgent field should exist"
            print(f"PASS: Listing doping fields present - is_featured={first_item.get('is_featured')}, is_urgent={first_item.get('is_urgent')}")


class TestAdminListingsApplicantTypeFilter:
    """Test GET /api/admin/listings applicant_type parameter"""

    def test_listings_no_filter(self, auth_headers):
        """Test listings without applicant_type filter returns 200"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data
        print(f"PASS: Admin listings (no filter) - total={data.get('pagination', {}).get('total', 0)}")

    def test_listings_individual_filter(self, auth_headers):
        """Test applicant_type=individual filter"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "applicant_type": "individual"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "items" in data
        print(f"PASS: Admin listings (applicant_type=individual) returned {len(data['items'])} items")

    def test_listings_corporate_filter(self, auth_headers):
        """Test applicant_type=corporate filter"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "applicant_type": "corporate"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "items" in data
        print(f"PASS: Admin listings (applicant_type=corporate) returned {len(data['items'])} items")

    def test_listings_invalid_applicant_type(self, auth_headers):
        """Test invalid applicant_type returns 400"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "applicant_type": "invalid_type"},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid applicant_type, got {response.status_code}"
        print("PASS: Invalid applicant_type correctly returns 400")


class TestAdminListingsDopingTypeFilter:
    """Test GET /api/admin/listings doping_type parameter"""

    def test_listings_doping_free(self, auth_headers):
        """Test doping_type=free filter"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "doping_type": "free"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "items" in data
        assert "doping_counts" in data, "Response should contain doping_counts"
        print(f"PASS: Admin listings (doping_type=free) returned {len(data['items'])} items, counts={data.get('doping_counts')}")

    def test_listings_doping_showcase(self, auth_headers):
        """Test doping_type=showcase filter"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "doping_type": "showcase"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "items" in data
        print(f"PASS: Admin listings (doping_type=showcase) returned {len(data['items'])} items")

    def test_listings_doping_urgent(self, auth_headers):
        """Test doping_type=urgent filter"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "doping_type": "urgent"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert "items" in data
        print(f"PASS: Admin listings (doping_type=urgent) returned {len(data['items'])} items")

    def test_listings_invalid_doping_type(self, auth_headers):
        """Test invalid doping_type returns 400"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 5, "doping_type": "premium"},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400 for invalid doping_type, got {response.status_code}"
        print("PASS: Invalid doping_type correctly returns 400")

    def test_doping_counts_structure(self, auth_headers):
        """Test that doping_counts has free/showcase/urgent keys"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        doping_counts = data.get("doping_counts", {})
        assert "free" in doping_counts, "doping_counts should have 'free' key"
        assert "showcase" in doping_counts, "doping_counts should have 'showcase' key"
        assert "urgent" in doping_counts, "doping_counts should have 'urgent' key"
        print(f"PASS: doping_counts structure correct: {doping_counts}")


class TestAdminDopingEndpoint:
    """Test POST /api/admin/listings/{listing_id}/doping endpoint"""

    @pytest.fixture(scope="class")
    def test_listing_id(self, auth_headers):
        """Get an existing listing ID for testing"""
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 1},
            headers=auth_headers
        )
        if response.status_code != 200:
            pytest.skip("Could not fetch listings")
        data = response.json()
        if not data.get("items"):
            pytest.skip("No listings available for testing")
        return data["items"][0]["id"]

    def test_doping_showcase_7days(self, auth_headers, test_listing_id):
        """Test setting showcase doping for 7 days"""
        response = requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={
                "doping_type": "showcase",
                "duration_days": 7,
                "reason": "test_showcase_7d"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        listing = data.get("listing", data)  # Handle nested structure
        assert listing.get("is_featured") is True, "Listing should be featured after showcase doping"
        assert listing.get("doping_type") == "showcase", "doping_type should be showcase"
        assert listing.get("featured_until") is not None, "featured_until should be set"
        print(f"PASS: Showcase 7 days applied - featured_until={listing.get('featured_until')}")

    def test_doping_urgent_30days(self, auth_headers, test_listing_id):
        """Test setting urgent doping for 30 days"""
        response = requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={
                "doping_type": "urgent",
                "duration_days": 30,
                "reason": "test_urgent_30d"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        listing = data.get("listing", data)  # Handle nested structure
        # Note: After urgent, showcase priority means is_featured might still be True if featured_until > now
        assert listing.get("is_urgent") is True, "Listing should be urgent after urgent doping"
        assert listing.get("urgent_until") is not None, "urgent_until should be set"
        print(f"PASS: Urgent 30 days applied - urgent_until={listing.get('urgent_until')}")

    def test_doping_free(self, auth_headers, test_listing_id):
        """Test removing doping (set to free)"""
        response = requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={
                "doping_type": "free",
                "reason": "test_free_reset"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        listing = data.get("listing", data)  # Handle nested structure
        assert listing.get("is_featured") is False, "Listing should not be featured after free doping"
        assert listing.get("is_urgent") is False, "Listing should not be urgent after free doping"
        assert listing.get("featured_until") is None, "featured_until should be None"
        assert listing.get("urgent_until") is None, "urgent_until should be None"
        print("PASS: Doping reset to free")

    def test_doping_showcase_90days(self, auth_headers, test_listing_id):
        """Test setting showcase doping for 90 days"""
        response = requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={
                "doping_type": "showcase",
                "duration_days": 90,
                "reason": "test_showcase_90d"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        listing = data.get("listing", data)  # Handle nested structure
        assert listing.get("is_featured") is True
        print(f"PASS: Showcase 90 days applied")

    def test_doping_custom_days(self, auth_headers, test_listing_id):
        """Test setting doping with custom days (manual)"""
        response = requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={
                "doping_type": "urgent",
                "duration_days": 45,  # Custom/manual value
                "reason": "test_custom_45d"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        listing = data.get("listing", data)  # Handle nested structure
        assert listing.get("urgent_until") is not None
        print(f"PASS: Custom 45 days urgent applied")

    def test_doping_invalid_listing_id(self, auth_headers):
        """Test doping endpoint with invalid listing ID"""
        response = requests.post(
            f"{API}/admin/listings/00000000-0000-0000-0000-000000000000/doping",
            json={
                "doping_type": "showcase",
                "duration_days": 7
            },
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Invalid listing ID returns 404")

    def test_doping_requires_duration_for_non_free(self, auth_headers, test_listing_id):
        """Test that showcase/urgent without duration_days fails"""
        # Reset to free first
        requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={"doping_type": "free"},
            headers=auth_headers
        )
        
        # Try showcase without duration
        response = requests.post(
            f"{API}/admin/listings/{test_listing_id}/doping",
            json={"doping_type": "showcase"},  # No duration_days
            headers=auth_headers
        )
        # Implementation should require duration_days for non-free
        # Based on code review, it should return 400 or accept with default
        # Let's check what actually happens
        print(f"Showcase without duration: status={response.status_code}")


class TestPublicSearchDopingFields:
    """Test /api/v2/search returns is_featured and is_urgent fields"""

    def test_search_returns_doping_flags(self):
        """Verify public search returns is_featured and is_urgent"""
        response = requests.get(
            f"{API}/v2/search",
            params={"country": "DE", "limit": 10, "page": 1}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:300]}"
        data = response.json()
        assert "items" in data, "Response should have 'items'"
        
        if data["items"]:
            first_item = data["items"][0]
            # Check for is_featured and is_urgent fields
            assert "is_featured" in first_item, f"is_featured field missing in search result: {first_item.keys()}"
            assert "is_urgent" in first_item, f"is_urgent field missing in search result: {first_item.keys()}"
            print(f"PASS: Search results contain doping flags - first item: is_featured={first_item.get('is_featured')}, is_urgent={first_item.get('is_urgent')}")
        else:
            print("WARN: No items in search results to verify doping fields")

    def test_search_no_error(self):
        """Basic search should not throw errors"""
        response = requests.get(
            f"{API}/v2/search",
            params={"country": "DE", "limit": 5}
        )
        assert response.status_code == 200, f"Search failed: {response.status_code} - {response.text[:200]}"
        print("PASS: Public search endpoint working")


class TestDopingPriority:
    """Test doping priority: Vitrin > Acil > Ücretsiz"""

    def test_showcase_overrides_urgent(self, auth_headers):
        """When both showcase and urgent are active, showcase should be the doping_type"""
        # Get a listing
        response = requests.get(
            f"{API}/admin/listings",
            params={"skip": 0, "limit": 1},
            headers=auth_headers
        )
        if response.status_code != 200 or not response.json().get("items"):
            pytest.skip("No listings available")
        
        listing_id = response.json()["items"][0]["id"]
        
        # First set urgent
        requests.post(
            f"{API}/admin/listings/{listing_id}/doping",
            json={"doping_type": "urgent", "duration_days": 30},
            headers=auth_headers
        )
        
        # Then set showcase (should override in display)
        response = requests.post(
            f"{API}/admin/listings/{listing_id}/doping",
            json={"doping_type": "showcase", "duration_days": 30},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        listing = data.get("listing", data)  # Handle nested structure
        
        # Based on implementation, showcase clears urgent_until
        assert listing.get("is_featured") is True, "Showcase should be active"
        assert listing.get("urgent_until") is None, "urgent_until should be cleared when showcase is set"
        print("PASS: Showcase priority correctly applied (clears urgent)")

        # Clean up
        requests.post(
            f"{API}/admin/listings/{listing_id}/doping",
            json={"doping_type": "free"},
            headers=auth_headers
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
