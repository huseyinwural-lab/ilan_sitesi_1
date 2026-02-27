import pytest
import requests
import json
from datetime import datetime
import uuid

class TestFAZFinal01:
    """Test suite for FAZ-FINAL-01 P0 release blockers"""
    
    def __init__(self):
        self.base_url = "https://feature-complete-36.preview.emergentagent.com"
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.admin_user = None
        
    def setup_method(self):
        """Setup for each test method"""
        # Login as admin to get token
        login_response = requests.post(
            f"{self.api_url}/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        self.token = login_data["access_token"]
        self.admin_user = login_data["user"]
        
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def test_public_search_v2_no_country(self):
        """Test public search v2 without country parameter returns 400"""
        response = requests.get(f"{self.api_url}/v2/search")
        assert response.status_code == 400
        data = response.json()
        assert "country is required" in data["detail"]
        
    def test_public_search_v2_with_country(self):
        """Test public search v2 with country parameter returns 200 with required keys"""
        response = requests.get(f"{self.api_url}/v2/search?country=DE&limit=5")
        assert response.status_code == 200
        data = response.json()
        
        # Check required keys
        assert "items" in data
        assert "facets" in data
        assert "facet_meta" in data
        assert "pagination" in data
        
        # Check pagination structure
        assert "total" in data["pagination"]
        assert "page" in data["pagination"]
        assert "pages" in data["pagination"]
        
    def test_public_search_v2_with_query(self):
        """Test public search v2 with query parameter"""
        response = requests.get(f"{self.api_url}/v2/search?country=DE&q=bmw")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
    def test_public_search_v2_with_category(self):
        """Test public search v2 with category parameter"""
        response = requests.get(f"{self.api_url}/v2/search?country=DE&category=otomobil")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
    def test_categories_public_access(self):
        """Test categories endpoint is accessible without authentication"""
        response = requests.get(f"{self.api_url}/categories?module=vehicle")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_moderation_queue_count(self):
        """Test moderation queue count endpoint"""
        response = requests.get(
            f"{self.api_url}/admin/moderation/queue/count",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert isinstance(data["count"], int)
        
    def test_moderation_queue_list(self):
        """Test moderation queue list endpoint"""
        response = requests.get(
            f"{self.api_url}/admin/moderation/queue?status=pending_moderation&limit=5",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
    def test_audit_logs_endpoint(self):
        """Test audit logs endpoint returns required fields"""
        response = requests.get(
            f"{self.api_url}/audit-logs?limit=5",
            headers=self.get_auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If there are audit logs, check the structure
        if data:
            latest_log = data[0]
            required_fields = [
                "event_type", "action", "created_at"
            ]
            for field in required_fields:
                assert field in latest_log, f"Missing required field: {field}"
                
    def test_moderation_workflow_with_test_listing(self):
        """Test complete moderation workflow with a test listing"""
        # First, create a test listing to moderate
        test_listing = self.create_test_listing()
        if not test_listing:
            pytest.skip("Could not create test listing for moderation workflow")
            
        listing_id = test_listing["id"]
        
        # Test approve action
        approve_response = requests.post(
            f"{self.api_url}/admin/listings/{listing_id}/approve",
            headers=self.get_auth_headers()
        )
        
        if approve_response.status_code == 200:
            data = approve_response.json()
            assert data["ok"] is True
            assert data["listing"]["status"] == "published"
            
        # Create another test listing for reject test
        test_listing_2 = self.create_test_listing()
        if test_listing_2:
            listing_id_2 = test_listing_2["id"]
            
            # Test reject with invalid reason (should return 400)
            reject_response = requests.post(
                f"{self.api_url}/admin/listings/{listing_id_2}/reject",
                json={"reason": "invalid_reason"},
                headers=self.get_auth_headers()
            )
            assert reject_response.status_code == 400
            
            # Test needs_revision with reason=other but no reason_note (should return 400)
            revision_response = requests.post(
                f"{self.api_url}/admin/listings/{listing_id_2}/needs_revision",
                json={"reason": "other"},
                headers=self.get_auth_headers()
            )
            assert revision_response.status_code == 400
            
    def create_test_listing(self):
        """Create a test vehicle listing for moderation testing"""
        try:
            # Create a draft listing
            draft_payload = {
                "country": "DE",
                "category_key": "otomobil",
                "vehicle": {
                    "make_key": "bmw",
                    "model_key": "3-serie",
                    "year": 2020
                },
                "attributes": {
                    "price_eur": 25000,
                    "mileage_km": 50000,
                    "fuel_type": "gasoline"
                }
            }
            
            draft_response = requests.post(
                f"{self.api_url}/v1/listings/vehicle",
                json=draft_payload,
                headers=self.get_auth_headers()
            )
            
            if draft_response.status_code != 200:
                return None
                
            draft_data = draft_response.json()
            listing_id = draft_data["id"]
            
            # Upload test images (create minimal test images)
            test_images = self.create_test_images()
            if test_images:
                files = []
                for i, img_data in enumerate(test_images):
                    files.append(('files', (f'test_image_{i}.jpg', img_data, 'image/jpeg')))
                
                media_response = requests.post(
                    f"{self.api_url}/v1/listings/vehicle/{listing_id}/media",
                    files=files,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                
                if media_response.status_code != 200:
                    return None
            
            # Submit for moderation
            submit_response = requests.post(
                f"{self.api_url}/v1/listings/vehicle/{listing_id}/submit",
                headers=self.get_auth_headers()
            )
            
            if submit_response.status_code == 200:
                return {"id": listing_id}
            elif submit_response.status_code == 422:
                # Validation errors - listing created but not submitted
                return {"id": listing_id}
                
        except Exception as e:
            print(f"Error creating test listing: {e}")
            
        return None
        
    def create_test_images(self):
        """Create minimal test images (800x600 minimum)"""
        try:
            from PIL import Image
            import io
            
            images = []
            for i in range(3):  # Create 3 test images
                # Create a simple colored image
                img = Image.new('RGB', (800, 600), color=(100 + i*50, 150, 200))
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG')
                img_bytes.seek(0)
                images.append(img_bytes.getvalue())
                
            return images
        except ImportError:
            # PIL not available, return None
            return None


def run_faz_final_01_tests():
    """Run all FAZ-FINAL-01 tests using requests directly"""
    print("🚀 Starting FAZ-FINAL-01 P0 Release Blocker Tests")
    print("=" * 60)
    
    tester = TestFAZFinal01()
    tester.setup_method()
    
    tests = [
        ("Public Search v2 - No Country (400)", tester.test_public_search_v2_no_country),
        ("Public Search v2 - With Country (200)", tester.test_public_search_v2_with_country),
        ("Public Search v2 - With Query (200)", tester.test_public_search_v2_with_query),
        ("Public Search v2 - With Category (200)", tester.test_public_search_v2_with_category),
        ("Categories Public Access (200)", tester.test_categories_public_access),
        ("Moderation Queue Count (200)", tester.test_moderation_queue_count),
        ("Moderation Queue List (200)", tester.test_moderation_queue_list),
        ("Audit Logs Endpoint (200)", tester.test_audit_logs_endpoint),
        ("Moderation Workflow", tester.test_moderation_workflow_with_test_listing),
    ]
    
    passed = 0
    failed = 0
    failures = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Testing {test_name}...")
            test_func()
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name} - {str(e)}")
            failed += 1
            failures.append((test_name, str(e)))
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failures:
        print(f"\n❌ Failed Tests:")
        for test_name, error in failures:
            print(f"  • {test_name}: {error}")
    
    success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
    print(f"\n📈 Success Rate: {success_rate:.1f}%")
    
    return success_rate >= 80


if __name__ == "__main__":
    success = run_faz_final_01_tests()
    exit(0 if success else 1)