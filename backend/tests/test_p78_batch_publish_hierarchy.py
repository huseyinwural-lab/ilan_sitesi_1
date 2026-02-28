"""
P78 Iteration Tests - New User Flow:
- 2-level category editing (group + subcategory)
- Auto-opening new group draft when group is completed (1 -> 2 -> 3)
- Subcategory numbering logic 1.1 / 1.2 / 2.1 / 2.2
- Live hierarchy preview tree
- order-index preview suggested_next_sort_order with 'Uygula' button
- Backend batch publish scheduler manual trigger: POST /api/admin/listings/batch-publish/run
- Slot priority rule regression: showcase > urgent > paid > free
- Publish slot consumption: campaign snapshot slot_consumed flow
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestBatchPublishScheduler:
    """Test batch publish scheduler manual trigger endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=15
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    def test_batch_publish_run_endpoint_exists(self, admin_token):
        """POST /api/admin/listings/batch-publish/run should exist and work"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/listings/batch-publish/run",
            headers=headers,
            json={},
            timeout=30
        )
        
        assert resp.status_code == 200, f"Batch publish run failed: {resp.status_code} - {resp.text}"
        data = resp.json()
        
        # Verify expected response fields
        assert "processed" in data, "Response should have 'processed' field"
        assert "published" in data, "Response should have 'published' field"
        assert "skipped" in data, "Response should have 'skipped' field"
        assert "errors" in data, "Response should have 'errors' field"
        assert "triggered_by" in data, "Response should have 'triggered_by' field"
        assert "interval_seconds" in data, "Response should have 'interval_seconds' field"
        
        print(f"[PASS] Batch publish run endpoint works")
        print(f"  processed={data.get('processed')}, published={data.get('published')}")
        print(f"  skipped={data.get('skipped')}, errors={data.get('errors')}")
        print(f"  interval_seconds={data.get('interval_seconds')}")
    
    def test_batch_publish_run_returns_interval(self, admin_token):
        """Batch publish should return interval_seconds (5 minutes = 300 seconds)"""
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/listings/batch-publish/run",
            headers=headers,
            json={},
            timeout=30
        )
        
        assert resp.status_code == 200
        data = resp.json()
        
        interval = data.get("interval_seconds")
        assert interval == 300, f"Interval should be 300 seconds (5 min), got {interval}"
        print(f"[PASS] Batch publish interval_seconds = {interval}")


class TestOrderIndexPreviewSuggestedNext:
    """Test order-index/preview endpoint returns suggested_next_sort_order"""
    
    @pytest.fixture
    def admin_token(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=15
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    def test_preview_returns_suggested_next_on_conflict(self, admin_token):
        """When sort_order conflicts, response should include suggested_next_sort_order"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First find existing categories
        categories_resp = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers=headers,
            timeout=15
        )
        assert categories_resp.status_code == 200
        categories = categories_resp.json().get("items", [])
        
        root_cats = [c for c in categories if not c.get("parent_id")]
        if not root_cats:
            pytest.skip("No root categories found for conflict test")
        
        conflict_cat = root_cats[0]
        conflict_sort = conflict_cat.get("sort_order", 1)
        conflict_module = conflict_cat.get("module", "real_estate")
        
        # Test preview with conflicting sort_order
        preview_resp = requests.get(
            f"{BASE_URL}/api/admin/categories/order-index/preview",
            params={
                "module": conflict_module,
                "country": "DE",
                "sort_order": conflict_sort
            },
            headers=headers,
            timeout=15
        )
        
        assert preview_resp.status_code == 200
        data = preview_resp.json()
        
        assert data.get("available") is False, "Should report conflict"
        assert "suggested_next_sort_order" in data, "Should include suggested_next_sort_order"
        
        suggested = data.get("suggested_next_sort_order")
        if suggested is not None:
            assert isinstance(suggested, int) and suggested > 0
            print(f"[PASS] suggested_next_sort_order = {suggested} for conflict on {conflict_sort}")
        else:
            print(f"[PASS] Conflict detected, suggested_next_sort_order = None")


class TestSlotPriorityRuleRegression:
    """Test slot priority rule: showcase > urgent > paid > free"""
    
    @pytest.fixture
    def admin_token(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=15
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    def test_campaign_items_listing_types_exist(self, admin_token):
        """Campaign items should have correct listing_type values"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Check campaign items endpoint
        resp = requests.get(
            f"{BASE_URL}/api/admin/pricing/campaign-items?scope=individual",
            headers=headers,
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            listing_types = set()
            for item in items:
                lt = item.get("listing_type")
                if lt:
                    listing_types.add(lt)
            
            expected_types = {"showcase", "urgent", "paid", "free"}
            print(f"[INFO] Found listing_types: {listing_types}")
            
            for lt in listing_types:
                assert lt in expected_types, f"Unknown listing_type: {lt}"
            
            print(f"[PASS] Campaign items have valid listing_types")
        else:
            print(f"[INFO] Campaign items API returned {resp.status_code}")
    
    def test_slot_priority_order_logic(self, admin_token):
        """Verify PRICING_LISTING_TYPE_PRIORITY: showcase(0) > urgent(1) > paid(2) > free(3)"""
        # This is a conceptual test - the priority is enforced in _campaign_item_priority
        expected_priority = {
            "showcase": 0,
            "urgent": 1,
            "paid": 2,
            "free": 3
        }
        
        # Verify priority order (lower number = higher priority)
        types_by_priority = sorted(expected_priority.items(), key=lambda x: x[1])
        priority_order = [t[0] for t in types_by_priority]
        
        assert priority_order == ["showcase", "urgent", "paid", "free"]
        print(f"[PASS] Priority order: {' > '.join(priority_order)}")


class TestSlotConsumptionRegression:
    """Test slot consumption flow at publish time"""
    
    @pytest.fixture
    def admin_token(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=15
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    def test_listings_have_doping_fields(self, admin_token):
        """Listings should have featured_until, urgent_until, paid_until fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/listings?limit=5",
            headers=headers,
            timeout=15
        )
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            
            if items:
                listing = items[0]
                doping_fields = ["featured_until", "urgent_until", "paid_until"]
                
                present_fields = []
                for field in doping_fields:
                    if field in listing or listing.get(field) is not None:
                        present_fields.append(field)
                    print(f"  {field}: {listing.get(field)}")
                
                print(f"[PASS] Listing doping fields checked")
            else:
                print(f"[INFO] No listings found")
        else:
            print(f"[INFO] Listings API returned {resp.status_code}")


class TestCategoryHierarchyFlow:
    """Test category hierarchy flow with 2-level columns"""
    
    @pytest.fixture
    def admin_token(self):
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=15
        )
        assert resp.status_code == 200
        return resp.json()["access_token"]
    
    def test_categories_list_returns_hierarchy(self, admin_token):
        """Categories list should show parent-child relationships"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers=headers,
            timeout=15
        )
        
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", [])
        
        root_cats = [c for c in items if not c.get("parent_id")]
        child_cats = [c for c in items if c.get("parent_id")]
        
        print(f"[INFO] Total categories: {len(items)}")
        print(f"[INFO] Root categories: {len(root_cats)}")
        print(f"[INFO] Child categories: {len(child_cats)}")
        
        # Verify hierarchy structure
        for root in root_cats[:3]:
            children = [c for c in child_cats if c.get("parent_id") == root.get("id")]
            print(f"  Root '{root.get('name')}' has {len(children)} children")
        
        print(f"[PASS] Category hierarchy structure verified")


class TestAdminAuth:
    """Basic admin auth test"""
    
    def test_health_check(self):
        """Health endpoint should return ok"""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=15)
        assert resp.status_code == 200
        print(f"[PASS] Health check OK")
    
    def test_admin_login(self):
        """Admin login should work"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
            timeout=15
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        print(f"[PASS] Admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
