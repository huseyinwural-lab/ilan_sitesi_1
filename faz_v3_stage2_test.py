import requests
import sys
import json
from datetime import datetime

class FAZV3Stage2Tester:
    def __init__(self, base_url="https://feature-complete-36.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        self.results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        test_headers = {}
        
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, params=data)
            elif method == 'POST':
                if files:
                    # For multipart file upload, don't set Content-Type
                    response = requests.post(url, files=files, headers=test_headers)
                else:
                    test_headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            
            result = {
                'test': name,
                'endpoint': endpoint,
                'method': method,
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'success': success,
                'response_data': None,
                'error': None
            }
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result['response_data'] = response.json()
                    print(f"   Response: {json.dumps(result['response_data'], indent=2)[:200]}...")
                except:
                    result['response_data'] = response.text
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    result['error'] = error_data
                    print(f"   Error: {error_data}")
                except:
                    result['error'] = response.text
                    print(f"   Error: {response.text}")
                
                self.failures.append(result)
            
            self.results.append(result)
            return success, result['response_data']

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            result = {
                'test': name,
                'endpoint': endpoint,
                'method': method,
                'expected_status': expected_status,
                'actual_status': None,
                'success': False,
                'response_data': None,
                'error': str(e)
            }
            self.failures.append(result)
            self.results.append(result)
            return False, {}

    def test_health_check(self):
        """Test /api/health endpoint"""
        return self.run_test("Health Check", "GET", "/health", 200)

    def test_vehicle_makes_de(self):
        """Test GET /api/v1/vehicle/makes?country=de"""
        success, data = self.run_test(
            "Vehicle Makes (DE)", 
            "GET", 
            "/v1/vehicle/makes", 
            200,
            data={"country": "de"}
        )
        
        if success and data:
            # Validate response structure
            if 'version' in data and 'items' in data and isinstance(data['items'], list):
                print(f"   ✅ Response has version and items array")
                print(f"   Version: {data['version']}")
                print(f"   Items count: {len(data['items'])}")
                
                # Check first few items for key+label structure
                for i, item in enumerate(data['items'][:3]):
                    if 'key' in item and 'label' in item:
                        print(f"   Item {i+1}: {item['key']} -> {item['label']}")
                    else:
                        print(f"   ⚠️ Item {i+1} missing key or label: {item}")
            else:
                print(f"   ⚠️ Response structure invalid - missing version or items array")
        
        return success, data

    def test_vehicle_models_bmw_de(self):
        """Test GET /api/v1/vehicle/models?make=bmw&country=de"""
        success, data = self.run_test(
            "Vehicle Models (BMW, DE)", 
            "GET", 
            "/v1/vehicle/models", 
            200,
            data={"make": "bmw", "country": "de"}
        )
        
        if success and data:
            # Validate response structure
            if 'make' in data and data['make'] == 'bmw' and 'items' in data:
                print(f"   ✅ Response has make='bmw' and items")
                print(f"   Make: {data['make']}")
                print(f"   Items count: {len(data['items'])}")
                
                # Check first few items
                for i, item in enumerate(data['items'][:3]):
                    print(f"   Model {i+1}: {item.get('key', 'N/A')} -> {item.get('label', 'N/A')}")
            else:
                print(f"   ⚠️ Response structure invalid - missing make or items")
        
        return success, data

    def login_admin(self):
        """Login to get auth token for admin endpoints"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"   Logged in as: {response['user']['full_name']} ({response['user']['role']})")
            return True
        return False

    def test_admin_vehicle_master_status(self):
        """Test GET /api/v1/admin/vehicle-master/status (requires auth)"""
        success, data = self.run_test(
            "Admin Vehicle Master Status", 
            "GET", 
            "/v1/admin/vehicle-master/status", 
            200
        )
        
        if success and data:
            if 'current' in data and 'recent_jobs' in data:
                print(f"   ✅ Response has current and recent_jobs")
                print(f"   Current version: {data.get('current', {}).get('version', 'N/A')}")
                print(f"   Recent jobs count: {len(data.get('recent_jobs', []))}")
            else:
                print(f"   ⚠️ Response structure invalid - missing current or recent_jobs")
        
        return success, data

    def test_admin_vehicle_master_validate_no_file(self):
        """Test POST /api/v1/admin/vehicle-master/validate without file (should return 400)"""
        return self.run_test(
            "Admin Vehicle Master Validate (No File)", 
            "POST", 
            "/v1/admin/vehicle-master/validate", 
            400
        )

    def test_admin_vehicle_master_validate_no_auth(self):
        """Test POST /api/v1/admin/vehicle-master/validate without auth token (should return 401/403)"""
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        # Try the request and check if we get 401 or 403 (both are valid auth errors)
        url = f"{self.api_url}/v1/admin/vehicle-master/validate"
        print(f"\n🔍 Testing Admin Vehicle Master Validate (No Auth)...")
        print(f"   URL: {url}")
        
        try:
            response = requests.post(url, json={})
            status_code = response.status_code
            
            # Accept both 401 and 403 as valid authentication errors
            if status_code in [401, 403]:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {status_code} (valid auth error)")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    response_data = response.text
                    print(f"   Response: {response.text[:200]}...")
                
                result = {
                    'test': "Admin Vehicle Master Validate (No Auth)",
                    'endpoint': "/v1/admin/vehicle-master/validate",
                    'method': "POST",
                    'expected_status': "401/403",
                    'actual_status': status_code,
                    'success': True,
                    'response_data': response_data,
                    'error': None
                }
                self.results.append(result)
                success = True
            else:
                print(f"❌ Failed - Expected 401 or 403, got {status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    error_data = response.text
                    print(f"   Error: {response.text}")
                
                result = {
                    'test': "Admin Vehicle Master Validate (No Auth)",
                    'endpoint': "/v1/admin/vehicle-master/validate", 
                    'method': "POST",
                    'expected_status': "401/403",
                    'actual_status': status_code,
                    'success': False,
                    'response_data': None,
                    'error': error_data
                }
                self.failures.append(result)
                self.results.append(result)
                success = False
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            result = {
                'test': "Admin Vehicle Master Validate (No Auth)",
                'endpoint': "/v1/admin/vehicle-master/validate",
                'method': "POST", 
                'expected_status': "401/403",
                'actual_status': None,
                'success': False,
                'response_data': None,
                'error': str(e)
            }
            self.failures.append(result)
            self.results.append(result)
            success = False
        
        self.tests_run += 1
        
        # Restore token
        self.token = original_token
        return success, {}

    def run_all_tests(self):
        """Run all FAZ-V3 Stage-2 tests"""
        print("🚀 Starting FAZ-V3 Stage-2 (REV-B) Backend API Smoke Tests")
        print("=" * 60)
        
        # 1. Health check
        health_success, _ = self.test_health_check()
        if not health_success:
            print("❌ Health check failed, stopping tests")
            return False
        
        # 2. Public vehicle endpoints (no auth required)
        print("\n📋 Testing Public Vehicle Endpoints...")
        self.test_vehicle_makes_de()
        self.test_vehicle_models_bmw_de()
        
        # 3. Admin endpoints (auth required)
        print("\n🔐 Testing Admin Endpoints...")
        
        # Login first
        if not self.login_admin():
            print("❌ Admin login failed, skipping admin tests")
        else:
            # Test with auth
            self.test_admin_vehicle_master_status()
            self.test_admin_vehicle_master_validate_no_file()
            
            # Test without auth
            self.test_admin_vehicle_master_validate_no_auth()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run}")
        
        if self.failures:
            print(f"\n❌ Failed tests ({len(self.failures)}):")
            for failure in self.failures:
                error_msg = failure.get('error', f'Status {failure.get("actual_status")} != {failure.get("expected_status")}')
                print(f"  • {failure['test']}: {error_msg}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Success rate: {success_rate:.1f}%")
        
        # Print detailed results for review
        print(f"\n📋 Detailed Results:")
        for result in self.results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"{status_icon} {result['test']}: {result['method']} {result['endpoint']} -> {result['actual_status']}")
        
        return success_rate >= 80

def main():
    tester = FAZV3Stage2Tester()
    
    if tester.run_all_tests():
        tester.print_summary()
        return 0 if tester.print_summary() else 1
    else:
        tester.print_summary()
        return 1

if __name__ == "__main__":
    sys.exit(main())