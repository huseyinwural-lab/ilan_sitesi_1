#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

class ReportsEngineAPITester:
    def __init__(self, base_url="https://multilist.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.failures = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")
        
        if not success:
            self.failures.append(result)

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            request_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            request_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}

            details = f"Status: {response.status_code}"
            if not success:
                details += f" (expected {expected_status})"
                if response_data and isinstance(response_data, dict):
                    error_msg = response_data.get('detail', str(response_data)[:200])
                    details += f" - {error_msg}"

            self.log_test(name, success, details)
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_admin_login(self) -> bool:
        """Test admin login and get token"""
        print("\n🔐 Testing Admin Login...")
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            user_info = response.get('user', {})
            self.log_test("Token Retrieved", True, f"Role: {user_info.get('role')}, Country Scope: {user_info.get('country_scope')}")
            return True
        
        self.log_test("Token Retrieved", False, "No access token in response")
        return False

    def test_admin_listings_basic(self) -> bool:
        """Test basic admin listings API"""
        print("\n📋 Testing Basic Admin Listings API...")
        
        success, response = self.run_test(
            "GET /admin/listings (basic)",
            "GET",
            "admin/listings",
            200
        )
        
        if success:
            items = response.get('items', [])
            pagination = response.get('pagination', {})
            total = pagination.get('total', 0)
            
            self.log_test("Response Structure Valid", True, 
                         f"Items: {len(items)}, Total: {total}")
            
            # Verify response structure
            if items:
                first_item = items[0]
                required_fields = ['id', 'title', 'status', 'country', 'owner_email', 'owner_role']
                missing_fields = [field for field in required_fields if field not in first_item]
                
                if not missing_fields:
                    self.log_test("Item Fields Complete", True, "All required fields present")
                else:
                    self.log_test("Item Fields Complete", False, f"Missing: {missing_fields}")
            else:
                self.log_test("Items Available", False, "No listings found")
        
        return success

    def test_admin_listings_filters(self) -> Dict[str, bool]:
        """Test admin listings API filters"""
        print("\n🔍 Testing Admin Listings Filters...")
        
        results = {}
        
        # Test country parameter
        success, response = self.run_test(
            "Country Filter (?country=DE)",
            "GET",
            "admin/listings?country=DE",
            200
        )
        results['country_filter'] = success
        
        # Test status filter
        success, response = self.run_test(
            "Status Filter (?status=published)",
            "GET",
            "admin/listings?status=published",
            200
        )
        results['status_filter'] = success
        
        # Test search query
        success, response = self.run_test(
            "Search Filter (?q=test)",
            "GET",
            "admin/listings?q=test",
            200
        )
        results['search_filter'] = success
        
        # Test dealer only filter
        success, response = self.run_test(
            "Dealer Only Filter (?dealer_only=true)",
            "GET",
            "admin/listings?dealer_only=true",
            200
        )
        results['dealer_only_filter'] = success
        
        # Test category filter
        success, response = self.run_test(
            "Category Filter (?category_id=otomobil)",
            "GET",
            "admin/listings?category_id=otomobil",
            200
        )
        results['category_filter'] = success
        
        # Test pagination
        success, response = self.run_test(
            "Pagination (?skip=0&limit=5)",
            "GET",
            "admin/listings?skip=0&limit=5",
            200
        )
        results['pagination'] = success
        
        if success and response:
            items = response.get('items', [])
            if len(items) <= 5:
                self.log_test("Pagination Limit Respected", True, f"Returned {len(items)} items (≤5)")
            else:
                self.log_test("Pagination Limit Respected", False, f"Returned {len(items)} items (>5)")
        
        # Test combined filters
        success, response = self.run_test(
            "Combined Filters (?country=DE&status=published&limit=10)",
            "GET",
            "admin/listings?country=DE&status=published&limit=10",
            200
        )
        results['combined_filters'] = success
        
        return results

    def test_listing_actions(self) -> Dict[str, bool]:
        """Test listing action endpoints"""
        print("\n⚡ Testing Listing Actions...")
        
        results = {}
        
        # First, get listings to find candidates for actions
        success, response = self.run_test(
            "Get Listings for Actions",
            "GET",
            "admin/listings?limit=20",
            200
        )
        
        if not success:
            self.log_test("Actions Test Setup", False, "Could not fetch listings")
            return {'force_unpublish': False, 'soft_delete': False}
        
        items = response.get('items', [])
        published_listing = None
        non_archived_listing = None
        
        # Find candidates
        for item in items:
            if item.get('status') == 'published' and not published_listing:
                published_listing = item
            if item.get('status') != 'archived' and not non_archived_listing:
                non_archived_listing = item
        
        # Test force-unpublish
        if published_listing:
            listing_id = published_listing['id']
            success, response = self.run_test(
                "Force Unpublish Action",
                "POST",
                f"admin/listings/{listing_id}/force-unpublish",
                200,
                data={"reason": "test_reason", "reason_note": "Testing force unpublish"}
            )
            results['force_unpublish'] = success
            
            if success:
                # Verify status changed
                success, verify_response = self.run_test(
                    "Verify Force-Unpublish Status",
                    "GET",
                    f"admin/listings?q={listing_id}",
                    200
                )
                if success:
                    verify_items = verify_response.get('items', [])
                    if verify_items and verify_items[0].get('status') == 'unpublished':
                        self.log_test("Status Changed to Unpublished", True, "Status correctly updated")
                    else:
                        current_status = verify_items[0].get('status') if verify_items else 'Not found'
                        self.log_test("Status Changed to Unpublished", False, f"Status: {current_status}")
        else:
            results['force_unpublish'] = False
            self.log_test("Force-Unpublish Test", False, "No published listing available")
        
        # Test soft-delete
        if non_archived_listing:
            listing_id = non_archived_listing['id']
            success, response = self.run_test(
                "Soft Delete Action",
                "POST",
                f"admin/listings/{listing_id}/soft-delete",
                200,
                data={"reason": "test_cleanup", "reason_note": "Testing soft delete"}
            )
            results['soft_delete'] = success
            
            if success:
                # Verify status changed to archived
                success, verify_response = self.run_test(
                    "Verify Soft-Delete Status",
                    "GET",
                    f"admin/listings?q={listing_id}",
                    200
                )
                if success:
                    verify_items = verify_response.get('items', [])
                    if verify_items and verify_items[0].get('status') == 'archived':
                        self.log_test("Status Changed to Archived", True, "Status correctly updated")
                    else:
                        current_status = verify_items[0].get('status') if verify_items else 'Not found'
                        self.log_test("Status Changed to Archived", False, f"Status: {current_status}")
        else:
            results['soft_delete'] = False
            self.log_test("Soft-Delete Test", False, "No non-archived listing available")
        
        return results

    def test_categories_api(self) -> bool:
        """Test categories API for filter dropdown"""
        print("\n📂 Testing Categories API...")
        
        success, response = self.run_test(
            "GET /categories?module=vehicle",
            "GET",
            "categories?module=vehicle",
            200
        )
        
        if success:
            categories = response if isinstance(response, list) else []
            self.log_test("Categories Retrieved", True, f"Count: {len(categories)}")
            
            # Check category structure
            if categories:
                first_cat = categories[0]
                required_fields = ['id']
                missing_fields = [field for field in required_fields if field not in first_cat]
                
                if not missing_fields:
                    self.log_test("Category Structure Valid", True, "Required fields present")
                else:
                    self.log_test("Category Structure Valid", False, f"Missing: {missing_fields}")
        
        return success

    def test_pagination_functionality(self) -> bool:
        """Test pagination with different page sizes"""
        print("\n📄 Testing Pagination Functionality...")
        
        # Test different page sizes
        page_sizes = [5, 10, 20]
        all_passed = True
        
        for size in page_sizes:
            success, response = self.run_test(
                f"Pagination Limit {size}",
                "GET",
                f"admin/listings?limit={size}",
                200
            )
            
            if success:
                items = response.get('items', [])
                pagination = response.get('pagination', {})
                
                if len(items) <= size:
                    self.log_test(f"Limit {size} Respected", True, f"Got {len(items)} items")
                else:
                    self.log_test(f"Limit {size} Respected", False, f"Got {len(items)} items (>{size})")
                    all_passed = False
                
                # Check pagination metadata
                if 'total' in pagination and 'skip' in pagination and 'limit' in pagination:
                    self.log_test(f"Pagination Metadata {size}", True, f"Total: {pagination['total']}")
                else:
                    self.log_test(f"Pagination Metadata {size}", False, "Missing pagination fields")
                    all_passed = False
            else:
                all_passed = False
        
        return all_passed

    def run_all_tests(self) -> Dict:
        """Run all tests and return summary"""
        print("🚀 Starting Admin Listings API Tests...")
        print(f"🌐 Base URL: {self.base_url}")
        
        # Test login first
        if not self.test_admin_login():
            print("❌ Login failed - cannot proceed with authenticated tests")
            return self.get_summary()
        
        # Test categories (used for filters)
        self.test_categories_api()
        
        # Test basic admin listings functionality
        self.test_admin_listings_basic()
        
        # Test filters
        self.test_admin_listings_filters()
        
        # Test pagination
        self.test_pagination_functionality()
        
        # Test listing actions
        self.test_listing_actions()
        
        return self.get_summary()

    def get_summary(self) -> Dict:
        """Get test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": f"{success_rate:.1f}%",
            "test_results": self.test_results,
            "failures": self.failures
        }

def main():
    """Main test execution"""
    tester = AdminListingsAPITester()
    
    try:
        summary = tester.run_all_tests()
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']}")
        
        # Print failed tests
        if summary['failures']:
            print("\n❌ FAILED TESTS:")
            for test in summary['failures']:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n✅ All tests passed!")
        
        # Return appropriate exit code
        return 0 if summary['failed_tests'] == 0 else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())