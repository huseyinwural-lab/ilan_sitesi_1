#!/usr/bin/env python3
"""
Sprint 1.1 Dealer Management Backend API Tests
Tests the dealer management endpoints as requested in the review.
"""

import requests
import json
import sys
from datetime import datetime

class DealerManagementTester:
    def __init__(self):
        # Get base URL from frontend/.env
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.split('=', 1)[1].strip()
                    break
        
        self.api_url = f"{self.base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        
        print(f"🔗 Base URL: {self.base_url}")
        print(f"🔗 API URL: {self.api_url}")

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.failures.append(name)

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            
            print(f"   {method} {url} -> {response.status_code}")
            
            if response.status_code == expected_status:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                try:
                    error_data = response.json()
                    return False, f"Status {response.status_code}: {error_data}"
                except:
                    return False, f"Status {response.status_code}: {response.text}"
                    
        except Exception as e:
            return False, f"Request failed: {str(e)}"

    def test_admin_login(self):
        """Test admin login with provided credentials"""
        print("\n🔐 Testing Admin Login...")
        
        success, response = self.make_request(
            'POST', 
            '/auth/login',
            data={"email": "admin@platform.com", "password": "Admin123!"},
            expected_status=200
        )
        
        if success and isinstance(response, dict) and 'access_token' in response:
            self.token = response['access_token']
            user = response.get('user', {})
            self.log_test(
                "Admin Login", 
                True, 
                f"Logged in as {user.get('full_name', 'Unknown')} ({user.get('role', 'Unknown')})"
            )
            return True
        else:
            self.log_test("Admin Login", False, str(response))
            return False

    def test_get_dealers_with_limit(self):
        """Test GET /api/admin/dealers?limit=5"""
        print("\n📋 Testing GET /api/admin/dealers?limit=5...")
        
        success, response = self.make_request('GET', '/admin/dealers?limit=5', expected_status=200)
        
        if success and isinstance(response, dict):
            items = response.get('items', [])
            pagination = response.get('pagination', {})
            
            has_items = 'items' in response
            has_pagination = 'pagination' in response
            
            if has_items and has_pagination:
                self.log_test(
                    "GET /api/admin/dealers?limit=5", 
                    True, 
                    f"Found {len(items)} dealers, pagination: {pagination}"
                )
                return True, response
            else:
                self.log_test(
                    "GET /api/admin/dealers?limit=5", 
                    False, 
                    f"Missing required fields. Response: {response}"
                )
                return False, response
        else:
            self.log_test("GET /api/admin/dealers?limit=5", False, str(response))
            return False, {}

    def test_get_dealers_by_status(self):
        """Test GET /api/admin/dealers?status=active"""
        print("\n🔍 Testing GET /api/admin/dealers?status=active...")
        
        success, response = self.make_request('GET', '/admin/dealers?status=active', expected_status=200)
        
        if success:
            self.log_test(
                "GET /api/admin/dealers?status=active", 
                True, 
                f"Response: {response}"
            )
            return True, response
        else:
            self.log_test("GET /api/admin/dealers?status=active", False, str(response))
            return False, {}

    def test_get_dealer_detail(self, dealers_data):
        """Test GET /api/admin/dealers/{id}"""
        print("\n👤 Testing GET /api/admin/dealers/{id}...")
        
        items = dealers_data.get('items', [])
        if not items:
            self.log_test("GET /api/admin/dealers/{id}", False, "No dealers found to test with")
            return False, {}
        
        dealer_id = items[0].get('id')
        if not dealer_id:
            self.log_test("GET /api/admin/dealers/{id}", False, "No dealer ID found")
            return False, {}
        
        success, response = self.make_request('GET', f'/admin/dealers/{dealer_id}', expected_status=200)
        
        if success and isinstance(response, dict):
            has_dealer = 'dealer' in response
            has_package = 'package' in response
            
            if has_dealer and has_package:
                self.log_test(
                    "GET /api/admin/dealers/{id}", 
                    True, 
                    f"Dealer detail retrieved with dealer and package info"
                )
                return True, response, dealer_id
            else:
                self.log_test(
                    "GET /api/admin/dealers/{id}", 
                    False, 
                    f"Missing dealer or package fields. Response: {response}"
                )
                return False, {}, dealer_id
        else:
            self.log_test("GET /api/admin/dealers/{id}", False, str(response))
            return False, {}, dealer_id

    def test_change_dealer_status(self, dealer_id):
        """Test POST /api/admin/dealers/{id}/status"""
        print("\n🔄 Testing POST /api/admin/dealers/{id}/status...")
        
        success, response = self.make_request(
            'POST', 
            f'/admin/dealers/{dealer_id}/status',
            data={"dealer_status": "suspended"},
            expected_status=200
        )
        
        if success:
            self.log_test(
                "POST /api/admin/dealers/{id}/status", 
                True, 
                f"Status changed to suspended. Response: {response}"
            )
            return True
        else:
            self.log_test("POST /api/admin/dealers/{id}/status", False, str(response))
            return False

    def test_audit_logs_verification(self):
        """Test audit logs for DEALER_STATUS_CHANGE event"""
        print("\n📝 Testing Audit Logs for DEALER_STATUS_CHANGE...")
        
        success, response = self.make_request('GET', '/audit-logs?event_type=DEALER_STATUS_CHANGE', expected_status=200)
        
        if success and isinstance(response, list):
            # Look for recent DEALER_STATUS_CHANGE events
            dealer_status_events = [log for log in response if log.get('event_type') == 'DEALER_STATUS_CHANGE']
            
            if dealer_status_events:
                latest_event = dealer_status_events[0]  # Should be most recent
                
                # Check required fields
                has_event_type = latest_event.get('event_type') == 'DEALER_STATUS_CHANGE'
                has_previous_status = 'previous_status' in latest_event
                has_new_status = 'new_status' in latest_event
                has_applied = latest_event.get('applied') == True
                
                if has_event_type and has_previous_status and has_new_status and has_applied:
                    self.log_test(
                        "Audit Logs DEALER_STATUS_CHANGE", 
                        True, 
                        f"Found event: {latest_event.get('previous_status')} -> {latest_event.get('new_status')}, applied={latest_event.get('applied')}"
                    )
                    return True
                else:
                    self.log_test(
                        "Audit Logs DEALER_STATUS_CHANGE", 
                        False, 
                        f"Missing required fields in audit log: {latest_event}"
                    )
                    return False
            else:
                self.log_test(
                    "Audit Logs DEALER_STATUS_CHANGE", 
                    False, 
                    "No DEALER_STATUS_CHANGE events found in audit logs"
                )
                return False
        else:
            self.log_test("Audit Logs DEALER_STATUS_CHANGE", False, str(response))
            return False

    def run_all_tests(self):
        """Run all dealer management tests"""
        print("🚀 Starting Sprint 1.1 Dealer Management Tests")
        print("=" * 60)
        
        # 1. Login
        if not self.test_admin_login():
            print("❌ Cannot proceed without authentication")
            return False
        
        # 2. Test GET /api/admin/dealers?limit=5
        dealers_success, dealers_data = self.test_get_dealers_with_limit()
        if not dealers_success:
            print("❌ Cannot proceed without dealers data")
            return False
        
        # 3. Test GET /api/admin/dealers?status=active
        self.test_get_dealers_by_status()
        
        # 4. Test GET /api/admin/dealers/{id}
        detail_success, detail_data, dealer_id = self.test_get_dealer_detail(dealers_data)
        if not detail_success:
            print("❌ Cannot proceed without dealer detail")
            return False
        
        # 5. Test POST /api/admin/dealers/{id}/status
        status_success = self.test_change_dealer_status(dealer_id)
        if not status_success:
            print("❌ Status change failed")
            return False
        
        # 6. Test audit logs verification
        self.test_audit_logs_verification()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failures:
            print(f"\n❌ Failed Tests ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 All tests passed!")
        elif success_rate >= 80:
            print("⚠️  Most tests passed, but some issues found")
        else:
            print("❌ Multiple test failures detected")
        
        return success_rate >= 80

def main():
    """Main test execution"""
    tester = DealerManagementTester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())