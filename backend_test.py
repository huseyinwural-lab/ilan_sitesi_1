import requests
import sys
import json
from datetime import datetime

class AdminPanelAPITester:
    def __init__(self, base_url="https://admin-marketplace-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.refresh_token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                
                self.failures.append({
                    'test': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'endpoint': endpoint
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failures.append({
                'test': name,
                'error': str(e),
                'endpoint': endpoint
            })
            return False, {}

    def test_health_check(self):
        """Test basic health check"""
        return self.run_test("Health Check", "GET", "/health", 200)

    def test_login_admin(self):
        """Test login with admin credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.refresh_token = response['refresh_token']
            self.user = response['user']
            print(f"   Logged in as: {self.user['full_name']} ({self.user['role']})")
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        return self.run_test("Get Current User", "GET", "/auth/me", 200)

    def test_dashboard_stats(self):
        """Test dashboard stats endpoint"""
        success, data = self.run_test("Dashboard Stats", "GET", "/dashboard/stats", 200)
        if success:
            print(f"   Users: {data.get('users', {}).get('total', 0)}")
            print(f"   Countries: {data.get('countries', {}).get('enabled', 0)}")
            print(f"   Feature Flags: {data.get('feature_flags', {}).get('enabled', 0)}")
        return success

    def test_get_users(self):
        """Test getting users list"""
        success, data = self.run_test("Get Users", "GET", "/users", 200)
        if success:
            print(f"   Found {len(data)} users")
        return success, data

    def test_get_countries(self):
        """Test getting countries"""
        success, data = self.run_test("Get Countries", "GET", "/countries", 200)
        if success:
            print(f"   Found {len(data)} countries")
            for country in data[:4]:  # Show first 4
                print(f"   - {country['code']}: {country['name'].get('tr', 'N/A')}")
        return success, data

    def test_get_feature_flags(self):
        """Test getting feature flags"""
        success, data = self.run_test("Get Feature Flags", "GET", "/feature-flags", 200)
        if success:
            modules = [f for f in data if f.get('scope') == 'module']
            features = [f for f in data if f.get('scope') == 'feature']
            print(f"   Found {len(modules)} modules, {len(features)} features")
        return success, data

    def test_feature_flag_toggle(self, flags_data):
        """Test toggling a feature flag"""
        if not flags_data:
            return False
        
        # Find first flag to toggle
        flag = flags_data[0] if flags_data else None
        if not flag:
            return False
            
        flag_id = flag['id']
        original_state = flag['is_enabled']
        
        success, response = self.run_test(
            f"Toggle Feature Flag ({flag['key']})",
            "POST",
            f"/feature-flags/{flag_id}/toggle",
            200
        )
        
        if success:
            new_state = response.get('is_enabled')
            print(f"   Toggled from {original_state} to {new_state}")
        
        return success

    def test_get_audit_logs(self):
        """Test getting audit logs"""
        success, data = self.run_test("Get Audit Logs", "GET", "/audit-logs", 200)
        if success:
            print(f"   Found {len(data)} audit log entries")
        return success

    def test_user_management(self, users_data):
        """Test user management operations"""
        if not users_data or len(users_data) < 2:
            return False
            
        # Find a non-admin user to test with
        test_user = None
        for user in users_data:
            if user['role'] != 'super_admin':
                test_user = user
                break
                
        if not test_user:
            return False
        
        user_id = test_user['id']
        
        # Test suspend
        success1, _ = self.run_test(
            f"Suspend User ({test_user['email']})",
            "POST",
            f"/users/{user_id}/suspend",
            200
        )
        
        # Test activate
        success2, _ = self.run_test(
            f"Activate User ({test_user['email']})",
            "POST", 
            f"/users/{user_id}/activate",
            200
        )
        
        return success1 and success2

    def test_country_by_code(self):
        """Test getting country by code"""
        return self.run_test("Get Country by Code (DE)", "GET", "/countries/code/DE", 200)

    def test_refresh_token(self):
        """Test token refresh"""
        if not self.refresh_token:
            return False
            
        success, response = self.run_test(
            "Refresh Token",
            "POST",
            "/auth/refresh",
            200,
            data={"refresh_token": self.refresh_token}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            print("   Token refreshed successfully")
        
        return success

def main():
    print("🚀 Starting Admin Panel API Tests")
    print("=" * 50)
    
    tester = AdminPanelAPITester()
    
    # Core authentication and health tests
    if not tester.test_health_check()[0]:
        print("❌ Health check failed, stopping tests")
        return 1
        
    if not tester.test_login_admin():
        print("❌ Login failed, stopping tests")
        return 1
    
    # User info test
    tester.test_get_current_user()
    
    # Dashboard and stats
    tester.test_dashboard_stats()
    
    # Get data for further tests
    users_success, users_data = tester.test_get_users()
    countries_success, countries_data = tester.test_get_countries()
    flags_success, flags_data = tester.test_get_feature_flags()
    
    # Feature operations
    if flags_data:
        tester.test_feature_flag_toggle(flags_data)
    
    # User management
    if users_data:
        tester.test_user_management(users_data)
    
    # Additional endpoints
    tester.test_get_audit_logs()
    tester.test_country_by_code()
    tester.test_refresh_token()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Tests completed: {tester.tests_passed}/{tester.tests_run}")
    
    if tester.failures:
        print(f"\n❌ Failed tests ({len(tester.failures)}):")
        for failure in tester.failures:
            error_msg = failure.get('error', f'Status {failure.get("actual")} != {failure.get("expected")}')
            print(f"  • {failure['test']}: {error_msg}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n📈 Success rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())