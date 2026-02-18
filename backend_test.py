#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

class MasterDataAPITester:
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
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=request_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_content": response.text[:200]}

            details = f"Status: {response.status_code}"
            if not success:
                details += f" (expected {expected_status})"
                if response_data:
                    details += f" - {response_data}"

            self.log_test(name, success, details)
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def login_admin(self) -> bool:
        """Login as admin user"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_master_data_engines(self):
        """Test all Master Data Engines functionality"""
        print("\n🔍 Testing Master Data Engines (SPRINT 5)")
        print("=" * 60)

        # Step 1: Login
        if not self.login_admin():
            print("❌ Admin login failed, stopping tests")
            return False

        # Step 2: Test Categories CRUD
        print("\n📁 Testing Categories CRUD...")
        if not self.test_categories_crud():
            return False

        # Step 3: Test Attributes CRUD  
        print("\n🏷️ Testing Attributes CRUD...")
        if not self.test_attributes_crud():
            return False

        # Step 4: Test Vehicle Makes CRUD
        print("\n🚗 Testing Vehicle Makes CRUD...")
        if not self.test_vehicle_makes_crud():
            return False

        # Step 5: Test Vehicle Models CRUD
        print("\n🚙 Testing Vehicle Models CRUD...")
        if not self.test_vehicle_models_crud():
            return False

        # Step 6: Test Public Search Integration
        print("\n🔍 Testing Public Search Integration...")
        if not self.test_public_search_integration():
            return False

        # Step 7: Test Listing Wizard Integration
        print("\n🧙 Testing Listing Wizard Integration...")
        if not self.test_listing_wizard_integration():
            return False

        return True

    def test_categories_crud(self):
        """Test Categories CRUD operations"""
        
        # List categories
        success, response = self.run_test(
            "List Categories",
            "GET",
            "admin/categories?country=DE",
            200
        )
        if not success:
            return False
            
        # Create category
        import time
        unique_suffix = str(int(time.time()))
        category_data = {
            "name": f"Test Category {unique_suffix}",
            "slug": f"test-category-{unique_suffix}",
            "country_code": "DE",
            "active_flag": True,
            "sort_order": 100
        }
        success, response = self.run_test(
            "Create Category",
            "POST",
            "admin/categories",
            201,
            data=category_data
        )
        
        if success and 'id' in response:
            category_id = response['id']
            
            # Update category
            update_data = {"name": "Updated Test Category"}
            success, _ = self.run_test(
                "Update Category",
                "PATCH",
                f"admin/categories/{category_id}",
                200,
                data=update_data
            )
            
            # Delete category (soft delete)
            success, _ = self.run_test(
                "Delete Category",
                "DELETE",
                f"admin/categories/{category_id}",
                200
            )
            
        return True

    def test_attributes_crud(self):
        """Test Attributes CRUD operations"""
        
        # First get a category to use
        success, categories = self.run_test(
            "Get Categories for Attributes",
            "GET",
            "admin/categories?country=DE",
            200
        )
        
        if not success or not categories.get('items'):
            print("❌ No categories found for attribute testing")
            return False
            
        category_id = categories['items'][0]['id']
        
        # List attributes
        success, response = self.run_test(
            "List Attributes",
            "GET",
            f"admin/attributes?country=DE&category_id={category_id}",
            200
        )
        
        # Create attribute
        attribute_data = {
            "category_id": category_id,
            "name": "Test Attribute",
            "key": "test_attribute",
            "type": "text",
            "required_flag": False,
            "filterable_flag": True,
            "country_code": "DE",
            "active_flag": True
        }
        success, response = self.run_test(
            "Create Attribute",
            "POST",
            "admin/attributes",
            201,
            data=attribute_data
        )
        
        if success and 'id' in response:
            attribute_id = response['id']
            
            # Update attribute
            update_data = {"name": "Updated Test Attribute"}
            success, _ = self.run_test(
                "Update Attribute",
                "PATCH",
                f"admin/attributes/{attribute_id}",
                200,
                data=update_data
            )
            
            # Delete attribute
            success, _ = self.run_test(
                "Delete Attribute",
                "DELETE",
                f"admin/attributes/{attribute_id}",
                200
            )
            
        return True

    def test_vehicle_makes_crud(self):
        """Test Vehicle Makes CRUD operations"""
        
        # List makes
        success, response = self.run_test(
            "List Vehicle Makes",
            "GET",
            "admin/vehicle-makes?country=DE",
            200
        )
        
        # Create make
        make_data = {
            "name": "Test Make",
            "slug": "test-make",
            "country_code": "DE",
            "active_flag": True
        }
        success, response = self.run_test(
            "Create Vehicle Make",
            "POST",
            "admin/vehicle-makes",
            201,
            data=make_data
        )
        
        if success and 'id' in response:
            make_id = response['id']
            
            # Update make
            update_data = {"name": "Updated Test Make"}
            success, _ = self.run_test(
                "Update Vehicle Make",
                "PATCH",
                f"admin/vehicle-makes/{make_id}",
                200,
                data=update_data
            )
            
            # Delete make
            success, _ = self.run_test(
                "Delete Vehicle Make",
                "DELETE",
                f"admin/vehicle-makes/{make_id}",
                200
            )
            
        return True

    def test_vehicle_models_crud(self):
        """Test Vehicle Models CRUD operations"""
        
        # First get a make to use
        success, makes = self.run_test(
            "Get Makes for Models",
            "GET",
            "admin/vehicle-makes?country=DE",
            200
        )
        
        if not success or not makes.get('items'):
            print("❌ No makes found for model testing")
            return False
            
        make_id = makes['items'][0]['id']
        
        # List models
        success, response = self.run_test(
            "List Vehicle Models",
            "GET",
            f"admin/vehicle-models?make_id={make_id}",
            200
        )
        
        # Create model
        model_data = {
            "make_id": make_id,
            "name": "Test Model",
            "slug": "test-model",
            "active_flag": True
        }
        success, response = self.run_test(
            "Create Vehicle Model",
            "POST",
            "admin/vehicle-models",
            201,
            data=model_data
        )
        
        if success and 'id' in response:
            model_id = response['id']
            
            # Update model
            update_data = {"name": "Updated Test Model"}
            success, _ = self.run_test(
                "Update Vehicle Model",
                "PATCH",
                f"admin/vehicle-models/{model_id}",
                200,
                data=update_data
            )
            
            # Delete model
            success, _ = self.run_test(
                "Delete Vehicle Model",
                "DELETE",
                f"admin/vehicle-models/{model_id}",
                200
            )
            
        return True

    def test_public_search_integration(self):
        """Test public search endpoints with master data filters"""
        
        # Test categories endpoint (public)
        success, response = self.run_test(
            "Public Categories List",
            "GET",
            "categories?module=vehicle&country=DE",
            200
        )
        
        # Test search endpoint with category filter
        success, response = self.run_test(
            "Search with Category Filter",
            "GET",
            "v2/search?country=DE&category=otomobil",
            200
        )
        
        # Test search endpoint with make filter
        success, response = self.run_test(
            "Search with Make Filter", 
            "GET",
            "v2/search?country=DE&make=bmw",
            200
        )
        
        # Test search endpoint with model filter
        success, response = self.run_test(
            "Search with Make and Model Filter",
            "GET", 
            "v2/search?country=DE&make=bmw&model=x5",
            200
        )
        
        return True

    def test_listing_wizard_integration(self):
        """Test listing wizard category integration"""
        
        # Test categories for wizard (same as public but testing separately)
        success, response = self.run_test(
            "Wizard Categories List",
            "GET",
            "categories?module=vehicle&country=DE",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} categories for wizard")
            # Check if we have both parent and child categories
            parent_cats = [cat for cat in response if not cat.get('parent_id')]
            child_cats = [cat for cat in response if cat.get('parent_id')]
            print(f"   Parent categories: {len(parent_cats)}, Child categories: {len(child_cats)}")
            
        return success

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(f"📊 MASTER DATA ENGINES TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print(f"\n❌ FAILURES ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  - {failure['test']}: {failure['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")

        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = MasterDataAPITester()
    
    try:
        success = tester.test_master_data_engines()
        tester.print_summary()
        
        # Save detailed results
        with open('/app/test_reports/backend_master_data_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'tests_run': tester.tests_run,
                    'tests_passed': tester.tests_passed,
                    'success_rate': f"{(tester.tests_passed/tester.tests_run*100):.1f}%"
                },
                'results': tester.test_results,
                'failures': tester.failures
            }, f, indent=2)
        
        return 0 if success and len(tester.failures) == 0 else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())