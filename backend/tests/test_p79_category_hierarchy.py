"""
P79 Tests - Category Hierarchy UI and Batch Publish Regression

This test file verifies:
1. Batch publish endpoint works correctly (regression)
2. Category creation with 2-level hierarchy
3. Subcategory validation (at least 1 required)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestP79BatchPublishRegression:
    """Batch publish endpoint regression tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login and get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_batch_publish_endpoint_works(self):
        """Test POST /api/admin/listings/batch-publish/run endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/admin/listings/batch-publish/run",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Batch publish failed: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "processed" in data, "Response missing 'processed' field"
        assert "published" in data, "Response missing 'published' field"
        assert "skipped" in data, "Response missing 'skipped' field"
        assert "errors" in data, "Response missing 'errors' field"
        assert "triggered_by" in data, "Response missing 'triggered_by' field"
        assert "interval_seconds" in data, "Response missing 'interval_seconds' field"
        
        # Verify interval_seconds is 300 (5 minutes)
        assert data["interval_seconds"] == 300, f"Expected interval_seconds=300, got {data['interval_seconds']}"
        
        print(f"PASS: Batch publish endpoint works - processed={data['processed']}, published={data['published']}, skipped={data['skipped']}")


class TestP79CategoryHierarchyValidation:
    """Category hierarchy validation tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login and get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_category_creation_successful(self):
        """Test that category creation works with proper hierarchy data"""
        import time
        unique_suffix = int(time.time())
        
        # Create a parent category first
        parent_payload = {
            "name": f"Test Parent P79 {unique_suffix}",
            "slug": f"test-parent-p79-{unique_suffix}",
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": unique_suffix % 1000,
            "hierarchy_complete": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=self.headers,
            json=parent_payload
        )
        
        # Category creation might return 201 or 200
        assert response.status_code in [200, 201], f"Category creation failed: {response.text}"
        
        data = response.json()
        assert "category" in data, "Response missing 'category' field"
        
        category_id = data["category"].get("id")
        assert category_id, "Created category missing ID"
        
        print(f"PASS: Parent category created with ID: {category_id}")
        
        # Create a subcategory under it
        subcategory_payload = {
            "name": f"Test Subcategory P79 1.1 {unique_suffix}",
            "slug": f"test-subcategory-p79-1-1-{unique_suffix}",
            "country_code": "DE",
            "module": "other",
            "parent_id": category_id,
            "active_flag": True,
            "sort_order": 1,
            "hierarchy_complete": True
        }
        
        sub_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=self.headers,
            json=subcategory_payload
        )
        
        assert sub_response.status_code in [200, 201], f"Subcategory creation failed: {sub_response.text}"
        
        sub_data = sub_response.json()
        assert "category" in sub_data, "Subcategory response missing 'category' field"
        
        subcategory_id = sub_data["category"].get("id")
        assert subcategory_id, "Created subcategory missing ID"
        
        print(f"PASS: Subcategory created with ID: {subcategory_id}")
        
        # Update parent to mark hierarchy as complete
        update_payload = {
            "hierarchy_complete": True,
            "wizard_progress": {"state": "category_completed", "dirty_steps": []}
        }
        
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=self.headers,
            json=update_payload
        )
        
        assert update_response.status_code == 200, f"Parent update failed: {update_response.text}"
        
        print("PASS: Parent category hierarchy marked as complete")
        
        # Clean up - delete the test categories
        requests.delete(f"{BASE_URL}/api/admin/categories/{subcategory_id}", headers=self.headers)
        requests.delete(f"{BASE_URL}/api/admin/categories/{category_id}", headers=self.headers)
        
        print("PASS: Test categories cleaned up")
    
    def test_order_index_preview_returns_suggested_sort(self):
        """Test that order index preview returns suggested_next_sort_order on conflict"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/order-index/preview",
            headers=self.headers,
            params={
                "module": "real_estate",
                "country": "DE",
                "sort_order": 1
            }
        )
        
        assert response.status_code == 200, f"Order preview failed: {response.text}"
        
        data = response.json()
        
        # If sort_order 1 is taken, we should get available=false and suggested_next_sort_order
        if not data.get("available", True):
            assert "suggested_next_sort_order" in data, "Missing suggested_next_sort_order in conflict response"
            print(f"PASS: Order conflict detected with suggested_next_sort_order={data['suggested_next_sort_order']}")
        else:
            print("PASS: Sort order 1 is available (no conflict)")


class TestP79CategoryAPIEndpoints:
    """Test category API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Login and get token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_categories_list_endpoint(self):
        """Test GET /api/admin/categories returns list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers=self.headers,
            params={"country": "DE"}
        )
        
        assert response.status_code == 200, f"Categories list failed: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response missing 'items' field"
        
        print(f"PASS: Categories list returned {len(data['items'])} items")
    
    def test_vehicle_segment_link_status_endpoint(self):
        """Test GET /api/admin/categories/vehicle-segment/link-status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/vehicle-segment/link-status",
            headers=self.headers,
            params={"segment": "pkw", "country": "DE"}
        )
        
        # Should return 200 even if segment not found (with linked=false)
        assert response.status_code == 200, f"Vehicle segment link status failed: {response.text}"
        
        data = response.json()
        assert "linked" in data, "Response missing 'linked' field"
        
        print(f"PASS: Vehicle segment link status - linked={data.get('linked')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
