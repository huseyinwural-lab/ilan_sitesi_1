#!/usr/bin/env python3
"""
P0 Regression Test: Backend Reachability and Admin Login
Test cases as specified in the review request:
1) GET {BASE}/api/health should be HTTP 200 and JSON includes database='mongo'
2) POST {BASE}/api/auth/login with admin credentials returns HTTP 200 with tokens and super_admin role
3) GET {BASE}/api/auth/me with Authorization Bearer token returns HTTP 200 with correct email
4) GET {BASE}/api/dashboard/stats with Authorization Bearer token returns HTTP 200 with users stats
"""

import requests
import json
import sys
from typing import Dict, Any, Tuple

class P0RegressionTester:
    def __init__(self):
        # Read base URL from frontend/.env
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        self.base_url = line.split('=', 1)[1].strip()
                        break
                else:
                    raise ValueError("REACT_APP_BACKEND_URL not found in frontend/.env")
        except Exception as e:
            print(f"❌ Failed to read base URL from frontend/.env: {e}")
            sys.exit(1)
            
        self.api_url = f"{self.base_url}/api"
        self.access_token = None
        self.test_results = []
        
        print(f"🔧 Base URL: {self.base_url}")
        print(f"🔧 API URL: {self.api_url}")

    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result for summary"""
        self.test_results.append({
            'name': test_name,
            'success': success,
            'details': details
        })
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Tuple[bool, int, Dict]:
        """Make HTTP request and return success, status_code, response_data"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        request_headers = {'Content-Type': 'application/json'}
        
        if headers:
            request_headers.update(headers)
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
                
            return True, response.status_code, response_data
            
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_1_health_check(self) -> bool:
        """Test 1: GET {BASE}/api/health should be HTTP 200 and JSON includes database='mongo'"""
        print("\n🔍 Test 1: Health Check")
        print(f"   URL: {self.api_url}/health")
        
        success, status_code, response_data = self.make_request('GET', '/health')
        
        if not success:
            print(f"❌ Request failed: {response_data.get('error', 'Unknown error')}")
            self.log_test_result("Health Check", False, f"Request failed: {response_data.get('error')}")
            return False
            
        if status_code != 200:
            print(f"❌ Expected status 200, got {status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Health Check", False, f"Status {status_code} != 200. Response: {response_data}")
            return False
            
        if response_data.get('database') != 'mongo':
            print(f"❌ Expected database='mongo', got database='{response_data.get('database')}'")
            print(f"   Full response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Health Check", False, f"database='{response_data.get('database')}' != 'mongo'")
            return False
            
        print(f"✅ Health check passed")
        print(f"   Status: {status_code}")
        print(f"   Database: {response_data.get('database')}")
        print(f"   Full response: {json.dumps(response_data, indent=2)}")
        self.log_test_result("Health Check", True, "HTTP 200, database='mongo'")
        return True

    def test_2_admin_login(self) -> bool:
        """Test 2: POST {BASE}/api/auth/login with admin credentials"""
        print("\n🔍 Test 2: Admin Login")
        print(f"   URL: {self.api_url}/auth/login")
        
        login_data = {
            "email": "admin@platform.com",
            "password": "Admin123!"
        }
        
        success, status_code, response_data = self.make_request('POST', '/auth/login', data=login_data)
        
        if not success:
            print(f"❌ Request failed: {response_data.get('error', 'Unknown error')}")
            self.log_test_result("Admin Login", False, f"Request failed: {response_data.get('error')}")
            return False
            
        if status_code != 200:
            print(f"❌ Expected status 200, got {status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Admin Login", False, f"Status {status_code} != 200. Response: {response_data}")
            return False
            
        # Check required fields
        required_fields = ['access_token', 'refresh_token', 'user']
        missing_fields = [field for field in required_fields if field not in response_data]
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Admin Login", False, f"Missing fields: {missing_fields}")
            return False
            
        # Check user role
        user_role = response_data.get('user', {}).get('role')
        if user_role != 'super_admin':
            print(f"❌ Expected user.role='super_admin', got '{user_role}'")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Admin Login", False, f"user.role='{user_role}' != 'super_admin'")
            return False
            
        # Store access token for subsequent tests
        self.access_token = response_data['access_token']
        
        print(f"✅ Admin login passed")
        print(f"   Status: {status_code}")
        print(f"   User role: {user_role}")
        print(f"   User email: {response_data.get('user', {}).get('email')}")
        print(f"   Access token: {self.access_token[:20]}...")
        self.log_test_result("Admin Login", True, f"HTTP 200, tokens received, role=super_admin")
        return True

    def test_3_auth_me(self) -> bool:
        """Test 3: GET {BASE}/api/auth/me with Authorization Bearer token"""
        print("\n🔍 Test 3: Get Current User (/auth/me)")
        print(f"   URL: {self.api_url}/auth/me")
        
        if not self.access_token:
            print("❌ No access token available (login test must have failed)")
            self.log_test_result("Auth Me", False, "No access token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.access_token}'}
        success, status_code, response_data = self.make_request('GET', '/auth/me', headers=headers)
        
        if not success:
            print(f"❌ Request failed: {response_data.get('error', 'Unknown error')}")
            self.log_test_result("Auth Me", False, f"Request failed: {response_data.get('error')}")
            return False
            
        if status_code != 200:
            print(f"❌ Expected status 200, got {status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Auth Me", False, f"Status {status_code} != 200. Response: {response_data}")
            return False
            
        # Check user email
        user_email = response_data.get('email')
        if user_email != 'admin@platform.com':
            print(f"❌ Expected user.email='admin@platform.com', got '{user_email}'")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Auth Me", False, f"user.email='{user_email}' != 'admin@platform.com'")
            return False
            
        print(f"✅ Auth me passed")
        print(f"   Status: {status_code}")
        print(f"   User email: {user_email}")
        print(f"   User role: {response_data.get('role')}")
        self.log_test_result("Auth Me", True, f"HTTP 200, email=admin@platform.com")
        return True

    def test_4_dashboard_stats(self) -> bool:
        """Test 4: GET {BASE}/api/dashboard/stats with Authorization Bearer token"""
        print("\n🔍 Test 4: Dashboard Stats")
        print(f"   URL: {self.api_url}/dashboard/stats")
        
        if not self.access_token:
            print("❌ No access token available (login test must have failed)")
            self.log_test_result("Dashboard Stats", False, "No access token available")
            return False
            
        headers = {'Authorization': f'Bearer {self.access_token}'}
        success, status_code, response_data = self.make_request('GET', '/dashboard/stats', headers=headers)
        
        if not success:
            print(f"❌ Request failed: {response_data.get('error', 'Unknown error')}")
            self.log_test_result("Dashboard Stats", False, f"Request failed: {response_data.get('error')}")
            return False
            
        if status_code != 200:
            print(f"❌ Expected status 200, got {status_code}")
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Dashboard Stats", False, f"Status {status_code} != 200. Response: {response_data}")
            return False
            
        # Check required users stats structure
        users_data = response_data.get('users', {})
        if 'total' not in users_data or 'active' not in users_data:
            print(f"❌ Expected users.total and users.active keys")
            print(f"   Users data: {users_data}")
            print(f"   Full response: {json.dumps(response_data, indent=2)}")
            self.log_test_result("Dashboard Stats", False, f"Missing users.total/users.active keys")
            return False
            
        print(f"✅ Dashboard stats passed")
        print(f"   Status: {status_code}")
        print(f"   Users total: {users_data.get('total')}")
        print(f"   Users active: {users_data.get('active')}")
        print(f"   Full response: {json.dumps(response_data, indent=2)}")
        self.log_test_result("Dashboard Stats", True, f"HTTP 200, users.total/users.active present")
        return True

    def run_all_tests(self) -> bool:
        """Run all P0 regression tests"""
        print("🚀 Starting P0 Regression Tests")
        print("=" * 60)
        
        # Run tests in sequence
        test1_result = self.test_1_health_check()
        test2_result = self.test_2_admin_login()
        test3_result = self.test_3_auth_me()
        test4_result = self.test_4_dashboard_stats()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 P0 REGRESSION TEST SUMMARY")
        print("=" * 60)
        
        passed_count = 0
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{status} - {result['name']}")
            if not result['success']:
                print(f"      Details: {result['details']}")
            else:
                passed_count += 1
                
        total_tests = len(self.test_results)
        success_rate = (passed_count / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n📈 Results: {passed_count}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if passed_count == total_tests:
            print("🎉 ALL P0 REGRESSION TESTS PASSED!")
            return True
        else:
            print("💥 SOME P0 REGRESSION TESTS FAILED!")
            return False

def main():
    tester = P0RegressionTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())