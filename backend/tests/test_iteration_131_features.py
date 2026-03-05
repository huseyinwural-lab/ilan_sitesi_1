"""
Iteration 131 Backend Feature Tests
=====================================
Tests for:
1. /api/admin/menu-items/health endpoint
2. /api/admin/site/content-layout/preset-events POST
3. /api/admin/site/content-layout/preset-events/summary GET
4. /api/admin/site/content-layout/revisions/{id}/policy-autofix POST
5. /api/public/geo/nearby-pois GET
6. /api/v1/listings/vehicle/{id} seller fields (rating/reviews_count/response_rate)
7. /api/v1/listings/vehicle/{id}/similar score + score_explanation + score_breakdown
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    for attempt in range(3):
        try:
            response = api_client.post(f"{BASE_URL}/api/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token") or data.get("token")
            time.sleep(1)
        except Exception as e:
            print(f"Login attempt {attempt+1} failed: {e}")
            time.sleep(2)
    pytest.skip("Authentication failed - skipping admin tests")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin auth headers"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestMenuItemsHealth:
    """Test /api/admin/menu-items/health endpoint"""

    def test_menu_items_health_endpoint_returns_200(self, api_client, admin_headers):
        """Menu health endpoint should return 200 with required fields"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/menu-items/health",
            headers=admin_headers,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "enabled" in data, "Response should contain 'enabled' field"
        assert "status" in data, "Response should contain 'status' field"
        assert "fallback_recommended" in data, "Response should contain 'fallback_recommended' field"
        
        # Verify types
        assert isinstance(data["enabled"], bool), "'enabled' should be boolean"
        assert isinstance(data["status"], str), "'status' should be string"
        assert isinstance(data["fallback_recommended"], bool), "'fallback_recommended' should be boolean"
        
        print(f"✓ Menu health: enabled={data['enabled']}, status={data['status']}, fallback_recommended={data['fallback_recommended']}")


class TestPresetEvents:
    """Test preset analytics endpoints"""

    def test_preset_events_post_creates_event(self, api_client, admin_headers):
        """POST /api/admin/site/content-layout/preset-events should create analytics event"""
        payload = {
            "preset_id": f"test-preset-{uuid.uuid4().hex[:8]}",
            "preset_label": "Test Preset Label",
            "persona": "individual",
            "variant": "A",
            "event_type": "apply",
            "page_type": "home",
            "country": "DE",
            "module": "global",
            "metadata_json": {"source": "backend_test"}
        }
        
        response = api_client.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset-events",
            headers=admin_headers,
            json=payload,
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "item" in data, "Response should contain 'item'"
        
        item = data["item"]
        assert item["preset_id"] == payload["preset_id"], "preset_id should match"
        assert item["persona"] == "individual", "persona should be normalized to lowercase"
        assert item["variant"] == "A", "variant should be normalized to uppercase"
        assert item["event_type"] == "apply", "event_type should match"
        
        print(f"✓ Preset event created: id={item.get('id')}")

    def test_preset_events_summary_returns_items(self, api_client, admin_headers):
        """GET /api/admin/site/content-layout/preset-events/summary should return summary"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset-events/summary",
            headers=admin_headers,
            params={
                "days": 90,
                "page_type": "home",
                "country": "DE",
                "module": "global"
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "items" in data, "Response should contain 'items'"
        assert "days" in data, "Response should contain 'days'"
        assert "total_events" in data, "Response should contain 'total_events'"
        
        assert isinstance(data["items"], list), "'items' should be a list"
        
        # If there are items, verify structure
        if data["items"]:
            item = data["items"][0]
            assert "preset_id" in item, "Item should have preset_id"
            assert "preset_label" in item, "Item should have preset_label"
            assert "persona" in item, "Item should have persona"
            assert "variant" in item, "Item should have variant"
            assert "apply_count" in item, "Item should have apply_count"
            assert "publish_count" in item, "Item should have publish_count"
            
        print(f"✓ Preset summary: {len(data['items'])} items, {data['total_events']} total events")


class TestPolicyAutoFix:
    """Test policy autofix endpoint"""

    def test_policy_autofix_for_listing_create_page(self, api_client, admin_headers):
        """POST /api/admin/site/content-layout/revisions/{id}/policy-autofix should work"""
        # First, get or create a listing_create_stepX page
        list_response = api_client.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=admin_headers,
            params={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": "global"
            },
            timeout=15
        )
        
        assert list_response.status_code == 200, f"Failed to list pages: {list_response.text}"
        
        pages = list_response.json().get("items", [])
        page_id = None
        
        if pages:
            page_id = pages[0]["id"]
        else:
            # Create new page
            create_response = api_client.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages",
                headers=admin_headers,
                json={
                    "page_type": "listing_create_stepX",
                    "country": "DE",
                    "module": "global"
                },
                timeout=15
            )
            if create_response.status_code in [200, 201]:
                page_id = create_response.json().get("item", {}).get("id")
        
        if not page_id:
            pytest.skip("Could not find or create listing_create_stepX page")
        
        # Get revisions for this page
        revisions_response = api_client.get(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions",
            headers=admin_headers,
            timeout=15
        )
        
        assert revisions_response.status_code == 200, f"Failed to get revisions: {revisions_response.text}"
        
        revisions = revisions_response.json().get("items", [])
        draft_revision = next((r for r in revisions if r["status"] == "draft"), None)
        
        if not draft_revision:
            # Create a draft revision
            create_draft_response = api_client.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
                headers=admin_headers,
                json={
                    "payload_json": {
                        "rows": [
                            {
                                "id": "row-test-1",
                                "columns": [
                                    {
                                        "id": "col-test-1",
                                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                        "components": [
                                            {
                                                "id": "cmp-default-test",
                                                "key": "listing.create.default-content",
                                                "props": {},
                                                "visibility": {"desktop": True, "tablet": True, "mobile": True}
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                },
                timeout=15
            )
            if create_draft_response.status_code in [200, 201]:
                draft_revision = create_draft_response.json().get("item")
        
        if not draft_revision:
            pytest.skip("Could not find or create draft revision")
        
        revision_id = draft_revision["id"]
        
        # Now test autofix endpoint
        autofix_response = api_client.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{revision_id}/policy-autofix",
            headers=admin_headers,
            timeout=20
        )
        
        assert autofix_response.status_code == 200, f"Expected 200, got {autofix_response.status_code}: {autofix_response.text}"
        
        data = autofix_response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "item" in data, "Response should contain 'item'"
        assert "report_before" in data, "Response should contain 'report_before'"
        assert "report_after" in data, "Response should contain 'report_after'"
        assert "auto_fix_actions" in data, "Response should contain 'auto_fix_actions'"
        
        assert isinstance(data["auto_fix_actions"], list), "'auto_fix_actions' should be a list"
        
        print(f"✓ Policy autofix executed: {len(data['auto_fix_actions'])} actions applied")


class TestNearbyPOIs:
    """Test /api/public/geo/nearby-pois endpoint"""

    def test_nearby_pois_returns_items(self, api_client):
        """GET /api/public/geo/nearby-pois should return POI items"""
        # Use Berlin coordinates
        response = api_client.get(
            f"{BASE_URL}/api/public/geo/nearby-pois",
            params={
                "lat": 52.52,
                "lng": 13.405,
                "radius_km": 2.0,
                "limit": 5
            },
            timeout=15
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "center" in data, "Response should contain 'center'"
        assert "radius_km" in data, "Response should contain 'radius_km'"
        assert "items" in data, "Response should contain 'items'"
        assert "source" in data, "Response should contain 'source'"
        
        assert isinstance(data["items"], list), "'items' should be a list"
        assert data["source"] in ["osm", "fallback"], "source should be 'osm' or 'fallback'"
        
        center = data["center"]
        assert "latitude" in center, "center should contain 'latitude'"
        assert "longitude" in center, "center should contain 'longitude'"
        
        print(f"✓ Nearby POIs: {len(data['items'])} items from source={data['source']}")


class TestVehicleListingSeller:
    """Test vehicle listing seller fields"""

    def test_vehicle_listing_detail_has_seller_fields(self, api_client):
        """GET /api/v1/listings/vehicle/{id} should return seller with rating/reviews_count/response_rate"""
        # First, find an active listing
        search_response = api_client.get(
            f"{BASE_URL}/api/public/search",
            params={"limit": 1, "country": "DE"},
            timeout=15
        )
        
        if search_response.status_code != 200:
            pytest.skip(f"Could not search for listings: {search_response.status_code}")
        
        items = search_response.json().get("items", [])
        if not items:
            pytest.skip("No active listings found for testing")
        
        listing_id = items[0].get("id")
        
        # Get listing detail
        detail_response = api_client.get(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}",
            timeout=15
        )
        
        assert detail_response.status_code == 200, f"Expected 200, got {detail_response.status_code}: {detail_response.text}"
        
        data = detail_response.json()
        assert "seller" in data, "Response should contain 'seller'"
        
        seller = data["seller"]
        assert "rating" in seller, "Seller should have 'rating' field"
        assert "reviews_count" in seller, "Seller should have 'reviews_count' field"
        assert "response_rate" in seller, "Seller should have 'response_rate' field"
        
        # Verify types
        assert isinstance(seller["rating"], (int, float)), "'rating' should be numeric"
        assert isinstance(seller["reviews_count"], int), "'reviews_count' should be integer"
        assert isinstance(seller["response_rate"], (int, float)), "'response_rate' should be numeric"
        
        print(f"✓ Listing {listing_id} seller: rating={seller['rating']}, reviews_count={seller['reviews_count']}, response_rate={seller['response_rate']}")


class TestVehicleSimilar:
    """Test vehicle similar listings endpoint"""

    def test_vehicle_similar_returns_score_fields(self, api_client):
        """GET /api/v1/listings/vehicle/{id}/similar should return items with score/score_explanation/score_breakdown"""
        # First, find an active listing
        search_response = api_client.get(
            f"{BASE_URL}/api/public/search",
            params={"limit": 1, "country": "DE"},
            timeout=15
        )
        
        if search_response.status_code != 200:
            pytest.skip(f"Could not search for listings: {search_response.status_code}")
        
        items = search_response.json().get("items", [])
        if not items:
            pytest.skip("No active listings found for testing")
        
        listing_id = items[0].get("id")
        
        # Get similar listings
        similar_response = api_client.get(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/similar",
            params={"limit": 5},
            timeout=15
        )
        
        assert similar_response.status_code == 200, f"Expected 200, got {similar_response.status_code}: {similar_response.text}"
        
        data = similar_response.json()
        assert "items" in data, "Response should contain 'items'"
        assert "fallback_used" in data, "Response should contain 'fallback_used'"
        
        similar_items = data["items"]
        assert isinstance(similar_items, list), "'items' should be a list"
        
        if similar_items:
            item = similar_items[0]
            assert "score" in item, "Similar item should have 'score' field"
            assert "score_explanation" in item, "Similar item should have 'score_explanation' field"
            assert "score_breakdown" in item, "Similar item should have 'score_breakdown' field"
            
            # Verify score_breakdown structure
            breakdown = item["score_breakdown"]
            assert isinstance(breakdown, dict), "'score_breakdown' should be a dict"
            assert "price_similarity" in breakdown, "breakdown should have 'price_similarity'"
            assert "city_match" in breakdown, "breakdown should have 'city_match'"
            assert "recency" in breakdown, "breakdown should have 'recency'"
            assert "make_model_match" in breakdown, "breakdown should have 'make_model_match'"
            assert "year_match" in breakdown, "breakdown should have 'year_match'"
            
            print(f"✓ Similar listings for {listing_id}: {len(similar_items)} items, first score={item['score']}")
        else:
            print(f"✓ Similar listings endpoint works but no similar items found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
