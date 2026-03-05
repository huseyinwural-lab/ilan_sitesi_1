"""
Iteration 129 Tests - Runtime Data Depth & Policy Auto-Fix

Features to test:
1. /api/v1/listings/vehicle/{id}: seller field has rating/reviews_count/response_rate
2. /api/v1/listings/vehicle/{id}/similar: item has score/score_explanation/score_breakdown
3. /api/public/geo/nearby-pois: returns 200 with items list (source osm/fallback)
4. /api/admin/site/content-layout/revisions/{id}/policy-report: checks[].fix_suggestion + suggested_fixes[]
5. /api/admin/site/content-layout/revisions/{id}/policy-autofix: returns 200, report_after/payload update
6. Preset persona/variant (individual/corporate) & preset analytics tracking (frontend-only, verifying backend doesn't break)
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuthentication:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0


# ============================================================
# 1. Vehicle Listing Detail - Seller Reputation Metrics
# ============================================================
class TestVehicleListingDetailSeller:
    """Test seller object in /api/v1/listings/vehicle/{id} has rating/reviews_count/response_rate"""
    
    def test_vehicle_detail_seller_reputation_fields(self):
        """Verify seller object contains rating, reviews_count, response_rate"""
        # First get a listing ID from search
        search_response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=5")
        assert search_response.status_code == 200
        
        items = search_response.json().get("items", [])
        if not items:
            pytest.skip("No listings available for testing")
        
        listing_id = items[0]["id"]
        
        # Fetch detail with preview mode
        detail_response = requests.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}?preview=1")
        
        # May return 404 if listing status is not published/active
        if detail_response.status_code == 404:
            pytest.skip("Listing not available (not published/active)")
        
        assert detail_response.status_code == 200
        data = detail_response.json()
        
        # Verify seller object exists
        assert "seller" in data, "Response should contain 'seller' object"
        seller = data["seller"]
        
        # Verify reputation fields exist (rating/reviews_count/response_rate)
        assert "rating" in seller, "seller should have 'rating' field"
        assert "reviews_count" in seller, "seller should have 'reviews_count' field"
        assert "response_rate" in seller, "seller should have 'response_rate' field"
        
        # Verify data types
        assert isinstance(seller["rating"], (int, float)), "rating should be numeric"
        assert isinstance(seller["reviews_count"], int), "reviews_count should be integer"
        assert isinstance(seller["response_rate"], (int, float)), "response_rate should be numeric"
        
        # Verify rating is within valid range (3.9 - 5.0 based on backend logic)
        assert 0 <= seller["rating"] <= 5.0, "rating should be between 0 and 5"
        
        # Verify reviews_count is non-negative
        assert seller["reviews_count"] >= 0, "reviews_count should be non-negative"
        
        # Verify response_rate is percentage (0-100)
        assert 0 <= seller["response_rate"] <= 100, "response_rate should be between 0 and 100"
        
        print(f"✓ Seller reputation: rating={seller['rating']}, reviews_count={seller['reviews_count']}, response_rate={seller['response_rate']}%")


# ============================================================
# 2. Similar Listings - Score + Explanation + Breakdown
# ============================================================
class TestSimilarListingsScoring:
    """Test /api/v1/listings/vehicle/{id}/similar returns score/score_explanation/score_breakdown"""
    
    def test_similar_listings_score_fields(self):
        """Verify similar listings have score, score_explanation, score_breakdown"""
        # First get a listing ID from search
        search_response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=5")
        assert search_response.status_code == 200
        
        items = search_response.json().get("items", [])
        if not items:
            pytest.skip("No listings available for testing")
        
        listing_id = items[0]["id"]
        
        # Fetch similar listings
        similar_response = requests.get(f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/similar?limit=8")
        
        if similar_response.status_code == 404:
            pytest.skip("Listing not available for similar endpoint")
        
        assert similar_response.status_code == 200
        data = similar_response.json()
        
        # Verify response structure
        assert "items" in data, "Response should contain 'items' array"
        items = data["items"]
        
        if not items:
            pytest.skip("No similar listings found for test listing")
        
        # Check first similar item for score fields
        first_item = items[0]
        
        assert "score" in first_item, "similar item should have 'score' field"
        assert "score_explanation" in first_item, "similar item should have 'score_explanation' field"
        assert "score_breakdown" in first_item, "similar item should have 'score_breakdown' field"
        
        # Verify score is integer (0-100)
        assert isinstance(first_item["score"], int), "score should be integer"
        assert 0 <= first_item["score"] <= 100, "score should be between 0 and 100"
        
        # Verify score_explanation is list of strings
        assert isinstance(first_item["score_explanation"], list), "score_explanation should be list"
        if first_item["score_explanation"]:
            assert isinstance(first_item["score_explanation"][0], str), "score_explanation items should be strings"
        
        # Verify score_breakdown is object with expected keys
        breakdown = first_item["score_breakdown"]
        assert isinstance(breakdown, dict), "score_breakdown should be dict"
        assert "price_similarity" in breakdown, "score_breakdown should have 'price_similarity'"
        assert "city_match" in breakdown, "score_breakdown should have 'city_match'"
        assert "recency" in breakdown, "score_breakdown should have 'recency'"
        
        print(f"✓ Similar listing score: {first_item['score']}/100")
        print(f"  Explanation: {first_item['score_explanation'][:2]}")
        print(f"  Breakdown: {breakdown}")


# ============================================================
# 3. Nearby POIs Endpoint
# ============================================================
class TestNearbyPoisEndpoint:
    """Test /api/public/geo/nearby-pois returns 200 with items (source osm/fallback)"""
    
    def test_nearby_pois_basic_request(self):
        """Verify nearby-pois returns 200 and items list"""
        # Use coordinates near Berlin
        lat = 52.52
        lng = 13.405
        
        response = requests.get(
            f"{BASE_URL}/api/public/geo/nearby-pois",
            params={"lat": lat, "lng": lng, "radius_km": 1.6, "limit": 6}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "items" in data, "Response should contain 'items' array"
        assert "source" in data, "Response should contain 'source' field (osm/fallback)"
        assert "center" in data, "Response should contain 'center' object"
        assert "radius_km" in data, "Response should contain 'radius_km' field"
        
        # Verify items is a list
        assert isinstance(data["items"], list), "items should be a list"
        
        # Verify source is osm or fallback
        assert data["source"] in ["osm", "fallback"], f"source should be osm or fallback, got {data['source']}"
        
        # Verify center coordinates
        center = data["center"]
        assert "latitude" in center and "longitude" in center
        assert abs(center["latitude"] - lat) < 0.001
        assert abs(center["longitude"] - lng) < 0.001
        
        print(f"✓ Nearby POIs: source={data['source']}, items_count={len(data['items'])}")
        
        # If items exist, verify structure
        if data["items"]:
            first_poi = data["items"][0]
            assert "name" in first_poi, "POI should have 'name' field"
            assert "distance_km" in first_poi, "POI should have 'distance_km' field"
            print(f"  First POI: {first_poi['name']} ({first_poi['distance_km']} km)")
    
    def test_nearby_pois_invalid_coordinates(self):
        """Verify nearby-pois returns 400 for invalid coordinates"""
        # Invalid latitude
        response = requests.get(
            f"{BASE_URL}/api/public/geo/nearby-pois",
            params={"lat": 91, "lng": 13.405}
        )
        assert response.status_code == 400
        
        # Invalid longitude
        response = requests.get(
            f"{BASE_URL}/api/public/geo/nearby-pois",
            params={"lat": 52.52, "lng": 181}
        )
        assert response.status_code == 400


# ============================================================
# 4. Policy Report - fix_suggestion + suggested_fixes[]
# ============================================================
class TestPolicyReportFixSuggestions:
    """Test policy report contains checks[].fix_suggestion + suggested_fixes[]"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_policy_report_fix_suggestion_fields(self):
        """Verify checks[] contain fix_suggestion and suggested_fixes[] exists"""
        module_name = f"TEST_i129_fix_suggestion_{int(time.time())}"
        
        # Create page
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Create valid draft
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [{
                                "id": "cmp-default",
                                "key": "listing.create.default-content",
                                "props": {}
                            }]
                        }]
                    }]
                }
            }
        )
        assert draft_response.status_code == 200
        draft_id = draft_response.json()["item"]["id"]
        
        # Get policy report
        report_response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-report",
            headers=self.headers
        )
        assert report_response.status_code == 200
        
        report = report_response.json()["report"]
        
        # Verify structure
        assert "checks" in report, "report should contain 'checks' array"
        assert "suggested_fixes" in report, "report should contain 'suggested_fixes' array"
        assert "policy" in report
        
        # Verify each check has fix_suggestion field
        for check in report["checks"]:
            assert "fix_suggestion" in check, f"Check '{check.get('id')}' missing fix_suggestion field"
        
        # Verify suggested_fixes is list (empty when all pass)
        assert isinstance(report["suggested_fixes"], list)
        
        print(f"✓ Policy report has {len(report['checks'])} checks, suggested_fixes={len(report['suggested_fixes'])}")


# ============================================================
# 5. Policy Auto-Fix Endpoint
# ============================================================
class TestPolicyAutoFix:
    """Test /api/admin/site/content-layout/revisions/{id}/policy-autofix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_policy_autofix_endpoint_returns_200(self):
        """Verify policy-autofix returns 200 with report_after and auto_fix_actions"""
        module_name = f"TEST_i129_autofix_{int(time.time())}"
        
        # Create page
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Create draft with valid payload to test autofix
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={
                "payload_json": {
                    "rows": [{
                        "id": "row-1",
                        "columns": [{
                            "id": "col-1",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [{
                                "id": "cmp-default",
                                "key": "listing.create.default-content",
                                "props": {}
                            }]
                        }]
                    }]
                }
            }
        )
        assert draft_response.status_code == 200
        draft_id = draft_response.json()["item"]["id"]
        
        # Call policy-autofix endpoint
        autofix_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-autofix",
            headers=self.headers
        )
        
        assert autofix_response.status_code == 200, f"Expected 200, got {autofix_response.status_code}: {autofix_response.text}"
        data = autofix_response.json()
        
        # Verify response structure
        assert "ok" in data, "Response should contain 'ok' field"
        assert data["ok"] == True
        assert "item" in data, "Response should contain updated 'item'"
        assert "report_after" in data, "Response should contain 'report_after'"
        assert "auto_fix_actions" in data, "Response should contain 'auto_fix_actions' list"
        
        # Verify report_after structure
        report_after = data["report_after"]
        assert "policy" in report_after
        assert "passed" in report_after
        assert "checks" in report_after
        
        # Verify auto_fix_actions is list
        assert isinstance(data["auto_fix_actions"], list)
        
        print(f"✓ Policy auto-fix: ok={data['ok']}, actions={len(data['auto_fix_actions'])}")
    
    def test_policy_autofix_not_applicable_for_non_listing_create(self):
        """Verify policy-autofix returns 400 for non listing_create_stepX page_type"""
        module_name = f"TEST_i129_autofix_na_{int(time.time())}"
        
        # Create page with home type (not listing_create_stepX)
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "home",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Create draft
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={"payload_json": {"rows": []}}
        )
        assert draft_response.status_code == 200
        draft_id = draft_response.json()["item"]["id"]
        
        # Call policy-autofix - should return 400 (not applicable)
        autofix_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/policy-autofix",
            headers=self.headers
        )
        
        assert autofix_response.status_code == 400
        assert "policy_autofix_not_applicable" in autofix_response.json().get("detail", "")


# ============================================================
# 6. Preset Pack Persona/Variant Validation (Backend API)
# ============================================================
class TestPresetPackPayloads:
    """Test preset pack payloads with persona/variant combinations work via API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_listing_create_individual_variant_a_payload(self):
        """Test listing-create-stepx preset with individual persona, variant A"""
        module_name = f"TEST_i129_individual_a_{int(time.time())}"
        
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Simulate individual persona, variant A payload
        payload = {
            "rows": [
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "listing.create.default-content", "props": {}},
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "shared.text-block", "props": {"title": "Bireysel İlan Ver Akışı", "body": "Adımları tamamlayın."}}
                        ]
                    }]
                },
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "interactive.doping-selector", "props": {"available_dopings": ["Vitrin", "Acil", "Anasayfa"], "show_prices": True, "default_selected": "Vitrin"}},
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "shared.ad-slot", "props": {"placement": "AD_LOGIN_1"}}
                        ]
                    }]
                }
            ]
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={"payload_json": payload}
        )
        assert draft_response.status_code == 200, f"Individual A payload failed: {draft_response.json()}"
        print("✓ Individual persona + Variant A payload accepted")
    
    def test_listing_create_corporate_variant_b_payload(self):
        """Test listing-create-stepx preset with corporate persona, variant B"""
        module_name = f"TEST_i129_corporate_b_{int(time.time())}"
        
        page_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=self.headers,
            json={
                "page_type": "listing_create_stepX",
                "country": "DE",
                "module": module_name
            }
        )
        assert page_response.status_code in [200, 201]
        page_id = page_response.json()["item"]["id"]
        
        # Simulate corporate persona, variant B payload
        payload = {
            "rows": [
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "listing.create.default-content", "props": {}},
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "shared.text-block", "props": {"title": "Kurumsal İlan Yönetimi", "body": "Ofis ekibiniz için standart form ve ödeme adımları."}}
                        ]
                    }]
                },
                {
                    "id": f"row-{uuid.uuid4().hex[:8]}",
                    "columns": [{
                        "id": f"col-{uuid.uuid4().hex[:8]}",
                        "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                        "components": [
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "interactive.doping-selector", "props": {"available_dopings": ["Premium", "Vitrin", "Anasayfa"], "show_prices": True, "default_selected": "Premium"}},
                            {"id": f"cmp-{uuid.uuid4().hex[:8]}", "key": "shared.ad-slot", "props": {"placement": "AD_LOGIN_1"}}
                        ]
                    }]
                }
            ]
        }
        
        draft_response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=self.headers,
            json={"payload_json": payload}
        )
        assert draft_response.status_code == 200, f"Corporate B payload failed: {draft_response.json()}"
        print("✓ Corporate persona + Variant B payload accepted")


# ============================================================
# Basic Health & Search Endpoints
# ============================================================
class TestHealthAndSearch:
    """Basic health and search endpoint tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_search_v2_basic(self):
        """Test search v2 endpoint"""
        response = requests.get(f"{BASE_URL}/api/v2/search?country=DE&limit=5")
        assert response.status_code == 200
        assert "items" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
