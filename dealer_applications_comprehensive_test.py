#!/usr/bin/env python3
"""
Sprint 1.2 Dealer Applications Backend E2E Tests - Comprehensive Version

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

class DealerApplicationsComprehensiveTester:
    def __init__(self, base_url="https://category-fix-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.country_admin_token = None
        self.admin_user = None
        self.country_admin_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        self.test_results = {}

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
        
        self.test_results[name] = {"success": success, "details": details}

    def make_request(self, method, endpoint, token=None, data=None, params=None):
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

            try:
                return response.status_code, response.json()
            except:
                return response.status_code, response.text

        except Exception as e:
            print(f"   Request failed: {str(e)}")
            return None, str(e)

    def setup_authentication(self):
        """Setup admin and country admin authentication"""
        print("\n🔐 Setting up Authentication...")
        
        # Admin login
        status, response = self.make_request(
            'POST', '/auth/login',
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        
        if status == 200 and 'access_token' in response:
            self.admin_token = response['access_token']
            self.admin_user = response['user']
            self.log_test("Admin Login", True, f"Logged in as {self.admin_user['full_name']}")
        else:
            self.log_test("Admin Login", False, f"Status: {status}")
            return False
        
        # Country admin login
        status, response = self.make_request(
            'POST', '/auth/login',
            data={"email": "country_admin_fr@test.com", "password": "CountryAdmin123!"}
        )
        
        if status == 200 and 'access_token' in response:
            self.country_admin_token = response['access_token']
            self.country_admin_user = response['user']
            self.log_test("Country Admin Login", True, f"Logged in as {self.country_admin_user['email']} (scope: {self.country_admin_user.get('country_scope', [])})")
        else:
            self.log_test("Country Admin Login", False, f"Status: {status}")
        
        return True

    def get_test_applications(self):
        """Get current applications and identify test applications"""
        print("\n📋 Getting Test Applications...")
        
        status, response = self.make_request(
            'GET', '/admin/dealer-applications',
            token=self.admin_token,
            params={'limit': 20}
        )
        
        if status != 200:
            print(f"   Failed to get applications: {status}")
            return {}
        
        apps = response.get('items', [])
        test_apps = {}
        
        for app in apps:
            email = app.get('email', '')
            if 'test_reject_other_final@example.com' in email:
                test_apps['reject_other'] = app
            elif 'test_reject_duplicate_final@example.com' in email:
                test_apps['reject_duplicate'] = app
            elif 'test_approve_final@example.com' in email:
                test_apps['approve'] = app
            elif 'test_scope_de_final@example.com' in email:
                test_apps['scope_test'] = app
        
        print(f"   Found {len(test_apps)} test applications")
        for key, app in test_apps.items():
            print(f"   - {key}: {app['email']} ({app['country_code']}) - {app['status']}")
        
        return test_apps

    def run_comprehensive_tests(self):
        """Run all dealer application tests in sequence"""
        print("🚀 Starting Sprint 1.2 Dealer Applications Backend E2E Tests")
        print("=" * 70)
        
        # Setup
        if not self.setup_authentication():
            return False
        
        test_apps = self.get_test_applications()
        
        # Test Case 1: GET dealer applications list
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
            details = f"Status: 200, Found {items_count} items, total: {total}"
        else:
            details = f"Status: {status}, Response: {response}"
        
        self.log_test("1) GET /api/admin/dealer-applications?limit=5 -> 200 with items/pagination", success, details)
        
        # Test Case 2: Reject with missing note
        print("\n❌ Test Case 2: Reject with Missing Note...")
        if 'reject_other' in test_apps:
            app_id = test_apps['reject_other']['id']
            status, response = self.make_request(
                'POST', f'/admin/dealer-applications/{app_id}/reject',
                token=self.admin_token,
                data={"reason": "other"}  # Missing reason_note
            )
            
            success = status == 400
            details = f"Status: {status} (expected 400)"
            if response and isinstance(response, dict):
                details += f", Error: {response.get('detail', 'No detail')}"
        else:
            success = False
            details = "No test application available for reject_other test"
        
        self.log_test("2) POST reject with reason=other and missing note -> 400", success, details)
        
        # Test Case 3: Reject with valid reason
        print("\n❌ Test Case 3: Reject with Valid Reason...")
        if 'reject_duplicate' in test_apps:
            app_id = test_apps['reject_duplicate']['id']
            status, response = self.make_request(
                'POST', f'/admin/dealer-applications/{app_id}/reject',
                token=self.admin_token,
                data={"reason": "duplicate_application"}
            )
            
            success = status == 200 and response.get('ok') == True
            details = f"Status: {status}"
            if success:
                details += " - Application rejected successfully"
        else:
            success = False
            details = "No test application available for reject_duplicate test"
        
        self.log_test("3) POST reject with reason=duplicate_application -> 200 ok", success, details)
        
        # Test Case 4: Approve application
        print("\n✅ Test Case 4: Approve Application...")
        approved_dealer_id = None
        if 'approve' in test_apps:
            app_id = test_apps['approve']['id']
            status, response = self.make_request(
                'POST', f'/admin/dealer-applications/{app_id}/approve',
                token=self.admin_token
            )
            
            success = (status == 200 and 
                      response.get('ok') == True and
                      'dealer_user' in response and
                      'temp_password' in response['dealer_user'])
            
            if success:
                dealer_user = response['dealer_user']
                approved_dealer_id = dealer_user['id']
                details = f"Status: 200, Created dealer: {dealer_user['email']} (ID: {dealer_user['id']})"
            else:
                details = f"Status: {status}, Response: {response}"
        else:
            success = False
            details = "No test application available for approve test"
        
        self.log_test("4) POST approve -> 200 ok and returns dealer_user temp_password", success, details)
        
        # Test Case 5: Verify dealer user created
        print("\n👤 Test Case 5: Verify Dealer User Created...")
        if approved_dealer_id:
            # Check via admin/dealers endpoint
            status, response = self.make_request(
                'GET', '/admin/dealers',
                token=self.admin_token
            )
            
            dealer_found = False
            if status == 200:
                for dealer in response.get('items', []):
                    if dealer.get('id') == approved_dealer_id:
                        dealer_found = True
                        success = dealer.get('dealer_status') == 'active'
                        if success:
                            details = f"Dealer user verified: {dealer['email']}, dealer_status=active"
                        else:
                            details = f"Dealer user found but dealer_status={dealer.get('dealer_status')} (expected active)"
                        break
            
            if not dealer_found:
                success = False
                details = f"Dealer user with ID {approved_dealer_id} not found"
        else:
            success = False
            details = "No approved dealer ID available from previous test"
        
        self.log_test("5) Verify new dealer user exists with role=dealer and dealer_status=active", success, details)
        
        # Test Case 6: Verify audit logs
        print("\n📝 Test Case 6: Verify Audit Logs...")
        status, audit_logs = self.make_request(
            'GET', '/audit-logs',
            token=self.admin_token,
            params={'limit': 50}
        )
        
        if status == 200:
            approved_events = [log for log in audit_logs if log.get('event_type') == 'DEALER_APPLICATION_APPROVED' and log.get('applied') == True]
            rejected_events = [log for log in audit_logs if log.get('event_type') == 'DEALER_APPLICATION_REJECTED' and log.get('applied') == True]
            
            success = len(approved_events) > 0 and len(rejected_events) > 0
            details = f"Found {len(approved_events)} approved events, {len(rejected_events)} rejected events (applied=true)"
        else:
            success = False
            details = f"Failed to get audit logs: {status}"
        
        self.log_test("6) Verify audit_logs has event_type DEALER_APPLICATION_APPROVED/REJECTED with applied=true", success, details)
        
        # Test Case 7: Scope enforcement
        print("\n🚫 Test Case 7: Country Scope Enforcement...")
        if self.country_admin_token and 'scope_test' in test_apps:
            app_id = test_apps['scope_test']['id']
            # Try to approve DE app with FR country admin using country=DE parameter
            status, response = self.make_request(
                'POST', f'/admin/dealer-applications/{app_id}/approve',
                token=self.country_admin_token,  # FR country admin
                params={'country': 'DE'}  # Trying to access DE context
            )
            
            success = status == 403
            details = f"Status: {status} (expected 403 for FR admin trying to access DE country context)"
            if response and isinstance(response, dict):
                details += f", Error: {response.get('detail', 'No detail')}"
        else:
            success = False
            if not self.country_admin_token:
                details = "No country admin token available"
            else:
                details = "No DE test application available for scope test"
        
        self.log_test("7) Scope enforcement: country_admin scoped FR attempting approve DE app -> 403", success, details)
        
        # Results summary
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        for i, (test_name, result) in enumerate(self.test_results.items(), 1):
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} Test {i}: {test_name}")
            if result["details"]:
                print(f"   {result['details']}")
        
        print(f"\n📈 Overall Results: {self.tests_passed}/{self.tests_run} tests passed ({(self.tests_passed/self.tests_run)*100:.1f}%)")
        
        if self.failures:
            print(f"\n❌ Failed tests ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  • {failure}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = DealerApplicationsComprehensiveTester()
    success = tester.run_comprehensive_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())