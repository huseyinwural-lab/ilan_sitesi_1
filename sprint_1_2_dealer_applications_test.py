#!/usr/bin/env python3
"""
Sprint 1.2 Dealer Applications Backend E2E Tests

Test cases:
1) GET /api/admin/dealer-applications?limit=5 -> 200 with items/pagination
2) POST /api/admin/dealer-applications/{id}/reject with reason=other and missing note -> 400
3) POST reject with reason=duplicate_application -> 200 ok
4) Seed (or find) a pending app and POST approve -> 200 ok and returns dealer_user temp_password
5) Verify new dealer user exists with role=dealer and dealer_status=active
6) Verify audit_logs has event_type DEALER_APPLICATION_APPROVED / DEALER_APPLICATION_REJECTED with applied=true
7) Scope enforcement: country_admin scoped FR attempting approve DE app -> 403
"""

import requests
import sys
import json
import uuid
from datetime import datetime, timezone

class DealerApplicationsTester:
    def __init__(self, base_url="https://admin-v1-refactor.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.country_admin_token = None
        self.admin_user = None
        self.country_admin_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        self.test_app_id = None
        self.approved_dealer_id = None

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

    def make_request(self, method, endpoint, token=None, data=None, params=None, expected_status=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")

            if expected_status and response.status_code != expected_status:
                print(f"   Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Response: {response.text}")

            try:
                return response.status_code, response.json()
            except:
                return response.status_code, response.text

        except Exception as e:
            print(f"   Request failed: {str(e)}")
            return None, str(e)

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔐 Testing Admin Login...")
        status, response = self.make_request(
            'POST', '/auth/login',
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        
        success = status == 200 and 'access_token' in response
        if success:
            self.admin_token = response['access_token']
            self.admin_user = response['user']
            details = f"Logged in as {self.admin_user['full_name']} ({self.admin_user['role']})"
        else:
            details = f"Status: {status}, Response: {response}"
        
        self.log_test("Admin Login", success, details)
        return success

    def create_country_admin_user(self):
        """Create a country admin user for scope testing"""
        print("\n👤 Testing Country Admin Login...")
        
        # Try to login with the country admin we created
        country_admin_email = "country_admin_fr@test.com"
        status, response = self.make_request(
            'POST', '/auth/login',
            data={"email": country_admin_email, "password": "CountryAdmin123!"}
        )
        
        if status == 200:
            self.country_admin_token = response['access_token']
            self.country_admin_user = response['user']
            self.log_test("Country Admin Login", True, f"Logged in as {response['user']['email']} (scope: {response['user'].get('country_scope', [])})")
            return True
        else:
            self.log_test("Country Admin Login", False, f"Status: {status}, Response: {response}")
            return False

    def seed_test_dealer_application(self):
        """Seed a test dealer application for testing"""
        print("\n🌱 Seeding Test Dealer Application...")
        
        # We need to insert directly into MongoDB since there's no public API to create applications
        # For testing purposes, we'll use the admin API to check if applications exist
        
        # First, let's check existing applications
        status, response = self.make_request(
            'GET', '/admin/dealer-applications',
            token=self.admin_token,
            params={'limit': 10}
        )
        
        if status == 200:
            existing_apps = response.get('items', [])
            pending_apps = [app for app in existing_apps if app.get('status') == 'pending']
            
            if pending_apps:
                self.test_app_id = pending_apps[0]['id']
                self.log_test("Find Existing Pending Application", True, f"Found app ID: {self.test_app_id}")
                return True
            else:
                # Try to create a test application via direct MongoDB insertion
                # Since we can't do this via API, we'll simulate by using existing data
                self.log_test("Seed Test Application", False, "No pending applications found and cannot create via API")
                return False
        else:
            self.log_test("Seed Test Application", False, f"Failed to check applications: {status}")
            return False

    def test_1_get_dealer_applications(self):
        """Test Case 1: GET /api/admin/dealer-applications?limit=5 -> 200 with items/pagination"""
        print("\n📋 Test Case 1: GET Dealer Applications List...")
        
        status, response = self.make_request(
            'GET', '/admin/dealer-applications',
            token=self.admin_token,
            params={'limit': 5}
        )
        
        success = (status == 200 and 
                  'items' in response and 
                  'pagination' in response and
                  isinstance(response['items'], list))
        
        if success:
            items_count = len(response['items'])
            total = response['pagination'].get('total', 0)
            details = f"Found {items_count} items, total: {total}"
            
            # Store first pending application for later tests
            for app in response['items']:
                if app.get('status') == 'pending':
                    self.test_app_id = app['id']
                    break
        else:
            details = f"Status: {status}, Response: {response}"
        
        self.log_test("GET /api/admin/dealer-applications", success, details)
        return success

    def test_2_reject_with_missing_note(self):
        """Test Case 2: POST reject with reason=other and missing note -> 400"""
        print("\n❌ Test Case 2: Reject Application with Missing Note...")
        
        if not self.test_app_id:
            self.log_test("Reject with Missing Note", False, "No test application ID available")
            return False
        
        status, response = self.make_request(
            'POST', f'/admin/dealer-applications/{self.test_app_id}/reject',
            token=self.admin_token,
            data={"reason": "other"}  # Missing reason_note
        )
        
        success = status == 400
        details = f"Status: {status} (expected 400)"
        if not success and response:
            details += f", Response: {response}"
        
        self.log_test("Reject with Missing Note (400)", success, details)
        return success

    def test_3_reject_with_valid_reason(self):
        """Test Case 3: POST reject with reason=duplicate_application -> 200 ok"""
        print("\n❌ Test Case 3: Reject Application with Valid Reason...")
        
        if not self.test_app_id:
            self.log_test("Reject with Valid Reason", False, "No test application ID available")
            return False
        
        status, response = self.make_request(
            'POST', f'/admin/dealer-applications/{self.test_app_id}/reject',
            token=self.admin_token,
            data={"reason": "duplicate_application"}
        )
        
        success = status == 200 and response.get('ok') == True
        details = f"Status: {status}"
        if success:
            details += " - Application rejected successfully"
        elif response:
            details += f", Response: {response}"
        
        self.log_test("Reject with Valid Reason (200)", success, details)
        
        # If we rejected the test app, we need to find another pending one for approval test
        if success:
            self.find_another_pending_application()
        
        return success

    def find_another_pending_application(self):
        """Find another pending application for approval test"""
        print("\n🔍 Finding Another Pending Application...")
        
        status, response = self.make_request(
            'GET', '/admin/dealer-applications',
            token=self.admin_token,
            params={'limit': 20, 'status': 'pending'}
        )
        
        if status == 200:
            pending_apps = [app for app in response.get('items', []) if app.get('status') == 'pending']
            if pending_apps:
                self.test_app_id = pending_apps[0]['id']
                print(f"   Found another pending application: {self.test_app_id}")
                return True
        
        print("   No other pending applications found")
        return False

    def test_4_approve_application(self):
        """Test Case 4: POST approve -> 200 ok and returns dealer_user temp_password"""
        print("\n✅ Test Case 4: Approve Dealer Application...")
        
        if not self.test_app_id:
            self.log_test("Approve Application", False, "No test application ID available")
            return False
        
        status, response = self.make_request(
            'POST', f'/admin/dealer-applications/{self.test_app_id}/approve',
            token=self.admin_token
        )
        
        success = (status == 200 and 
                  response.get('ok') == True and
                  'dealer_user' in response and
                  'temp_password' in response['dealer_user'])
        
        if success:
            dealer_user = response['dealer_user']
            self.approved_dealer_id = dealer_user['id']
            details = f"Created dealer user: {dealer_user['email']} (ID: {dealer_user['id']})"
        else:
            details = f"Status: {status}, Response: {response}"
        
        self.log_test("Approve Application (200)", success, details)
        return success

    def test_5_verify_dealer_user_created(self):
        """Test Case 5: Verify new dealer user exists with role=dealer and dealer_status=active"""
        print("\n👤 Test Case 5: Verify Dealer User Created...")
        
        if not self.approved_dealer_id:
            self.log_test("Verify Dealer User", False, "No approved dealer ID available")
            return False
        
        # Get dealers list via admin/dealers endpoint (which includes dealer_status)
        status, response = self.make_request(
            'GET', '/admin/dealers',
            token=self.admin_token
        )
        
        if status != 200:
            self.log_test("Verify Dealer User", False, f"Failed to get dealers: {status}")
            return False
        
        dealer_user = None
        for dealer in response.get('items', []):
            if dealer.get('id') == self.approved_dealer_id:
                dealer_user = dealer
                break
        
        if not dealer_user:
            self.log_test("Verify Dealer User", False, "Dealer user not found in dealers list")
            return False
        
        # Check if user also exists in users list with role=dealer
        status, users = self.make_request(
            'GET', '/users',
            token=self.admin_token
        )
        
        user_record = None
        if status == 200:
            for user in users:
                if user.get('id') == self.approved_dealer_id:
                    user_record = user
                    break
        
        success = (dealer_user.get('dealer_status') == 'active' and 
                  user_record and user_record.get('role') == 'dealer')
        
        if success:
            details = f"User {dealer_user['email']}: role=dealer, dealer_status=active"
        else:
            details = f"User {dealer_user['email']}: dealer_status={dealer_user.get('dealer_status')}, role={user_record.get('role') if user_record else 'NOT_FOUND'}"
        
        self.log_test("Verify Dealer User Properties", success, details)
        return success

    def test_6_verify_audit_logs(self):
        """Test Case 6: Verify audit_logs has proper event types with applied=true"""
        print("\n📝 Test Case 6: Verify Audit Logs...")
        
        status, audit_logs = self.make_request(
            'GET', '/audit-logs',
            token=self.admin_token,
            params={'limit': 50}
        )
        
        if status != 200:
            self.log_test("Verify Audit Logs", False, f"Failed to get audit logs: {status}")
            return False
        
        # Look for dealer application events
        approved_events = [log for log in audit_logs if log.get('event_type') == 'DEALER_APPLICATION_APPROVED']
        rejected_events = [log for log in audit_logs if log.get('event_type') == 'DEALER_APPLICATION_REJECTED']
        
        # Check for applied=true
        approved_applied = [log for log in approved_events if log.get('applied') == True]
        rejected_applied = [log for log in rejected_events if log.get('applied') == True]
        
        success = len(approved_applied) > 0 and len(rejected_applied) > 0
        
        details = f"Found {len(approved_applied)} approved events, {len(rejected_applied)} rejected events (applied=true)"
        
        self.log_test("Verify Audit Logs Events", success, details)
        return success

    def test_7_scope_enforcement(self):
        """Test Case 7: Country admin scoped FR attempting approve DE app -> 403"""
        print("\n🚫 Test Case 7: Country Scope Enforcement...")
        
        if not self.country_admin_token:
            self.log_test("Scope Enforcement", False, "No country admin token available")
            return False
        
        # Find a DE application
        status, response = self.make_request(
            'GET', '/admin/dealer-applications',
            token=self.admin_token,
            params={'limit': 20}
        )
        
        if status != 200:
            self.log_test("Scope Enforcement", False, f"Failed to get applications: {status}")
            return False
        
        de_app = None
        for app in response.get('items', []):
            if app.get('country_code') == 'DE' and app.get('status') == 'pending':
                de_app = app
                break
        
        if not de_app:
            self.log_test("Scope Enforcement", False, "No DE pending application found for scope test")
            return False
        
        # Try to approve DE app with FR country admin
        status, response = self.make_request(
            'POST', f'/admin/dealer-applications/{de_app["id"]}/approve',
            token=self.country_admin_token
        )
        
        success = status == 403
        details = f"Status: {status} (expected 403 for cross-country access)"
        
        self.log_test("Country Scope Enforcement (403)", success, details)
        return success

    def run_all_tests(self):
        """Run all dealer application tests"""
        print("🚀 Starting Sprint 1.2 Dealer Applications Backend E2E Tests")
        print("=" * 70)
        
        # Setup
        if not self.test_admin_login():
            print("❌ Admin login failed, stopping tests")
            return False
        
        self.create_country_admin_user()
        
        # Main test cases
        self.test_1_get_dealer_applications()
        self.test_2_reject_with_missing_note()
        self.test_3_reject_with_valid_reason()
        self.test_4_approve_application()
        self.test_5_verify_dealer_user_created()
        self.test_6_verify_audit_logs()
        self.test_7_scope_enforcement()
        
        # Results
        print("\n" + "=" * 70)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run}")
        
        if self.failures:
            print(f"\n❌ Failed tests ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Success rate: {success_rate:.1f}%")
        
        return success_rate >= 80

def main():
    tester = DealerApplicationsTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())