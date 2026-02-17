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

    def test_reports_engine(self):
        """Test all Reports Engine functionality"""
        print("\n🔍 Testing Reports Engine (SPRINT 2.2)")
        print("=" * 60)

        # Step 1: Login
        if not self.login_admin():
            print("❌ Admin login failed, stopping tests")
            return False

        # Step 2: Get a published listing for testing
        success, listings_response = self.run_test(
            "Get Published Listings",
            "GET", 
            "admin/listings?status=published&limit=1",
            200
        )
        
        if not success or not listings_response.get('items'):
            print("❌ No published listings found for testing")
            return False
            
        test_listing_id = listings_response['items'][0]['id']
        print(f"📋 Using test listing: {test_listing_id}")

        # Step 3: Test public report creation (POST /api/reports)
        report_data = {
            "listing_id": test_listing_id,
            "reason": "spam",
            "reason_note": "Test report for automated testing"
        }
        
        success, report_response = self.run_test(
            "Create Report (Public)",
            "POST",
            "reports",
            200,
            data=report_data
        )
        
        if not success:
            print("❌ Report creation failed")
            return False
            
        report_id = report_response.get('report_id')
        if not report_id:
            print("❌ No report_id returned")
            return False
            
        print(f"📝 Created report: {report_id}")

        # Step 4: Test admin reports listing (GET /api/admin/reports)
        success, admin_reports = self.run_test(
            "Admin Reports List",
            "GET",
            "admin/reports",
            200
        )
        
        if not success:
            return False

        # Test with filters
        success, filtered_reports = self.run_test(
            "Admin Reports with Status Filter",
            "GET",
            "admin/reports?status=open",
            200
        )

        success, reason_filtered = self.run_test(
            "Admin Reports with Reason Filter", 
            "GET",
            "admin/reports?reason=spam",
            200
        )

        success, listing_filtered = self.run_test(
            "Admin Reports with Listing ID Filter",
            "GET", 
            f"admin/reports?listing_id={test_listing_id}",
            200
        )

        # Step 5: Test report detail (GET /api/admin/reports/{id})
        success, report_detail = self.run_test(
            "Admin Report Detail",
            "GET",
            f"admin/reports/{report_id}",
            200
        )

        if not success:
            return False

        # Step 6: Test report status change (POST /api/admin/reports/{id}/status)
        status_data = {
            "target_status": "in_review",
            "note": "Moving to review for automated testing"
        }
        
        success, status_response = self.run_test(
            "Report Status Change",
            "POST",
            f"admin/reports/{report_id}/status",
            200,
            data=status_data
        )

        # Step 7: Test country scope validation
        success, country_scope_test = self.run_test(
            "Country Scope Test (DE)",
            "GET",
            "admin/reports?country=DE",
            200
        )

        # Step 8: Test invalid status transition (should fail)
        invalid_status_data = {
            "target_status": "resolved", 
            "note": "Invalid transition test"
        }
        
        success, invalid_response = self.run_test(
            "Invalid Status Transition (should fail)",
            "POST",
            f"admin/reports/{report_id}/status", 
            400,  # Expecting 400 for invalid transition
            data=invalid_status_data
        )

        # Step 9: Test rate limiting (create multiple reports quickly)
        print("\n🚦 Testing Rate Limiting...")
        rate_limit_failures = 0
        for i in range(6):  # Should hit rate limit after 5
            success, rate_response = self.run_test(
                f"Rate Limit Test {i+1}",
                "POST",
                "reports",
                200 if i < 5 else 429,  # Expect 429 after 5 attempts
                data={
                    "listing_id": test_listing_id,
                    "reason": "other",
                    "reason_note": f"Rate limit test {i+1}"
                }
            )
            if not success and i >= 5:
                rate_limit_failures += 1

        # Step 10: Test report reasons validation
        invalid_reason_data = {
            "listing_id": test_listing_id,
            "reason": "invalid_reason",
            "reason_note": "Testing invalid reason"
        }
        
        success, invalid_reason_response = self.run_test(
            "Invalid Reason Test (should fail)",
            "POST",
            "reports",
            400,
            data=invalid_reason_data
        )

        # Step 11: Test 'other' reason without note (should fail)
        other_no_note_data = {
            "listing_id": test_listing_id,
            "reason": "other"
            # Missing reason_note
        }
        
        success, other_no_note_response = self.run_test(
            "Other Reason Without Note (should fail)",
            "POST", 
            "reports",
            400,
            data=other_no_note_data
        )

        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print(f"📊 REPORTS ENGINE TEST SUMMARY")
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
    tester = ReportsEngineAPITester()
    
    try:
        success = tester.test_reports_engine()
        tester.print_summary()
        
        # Save detailed results
        with open('/app/test_reports/backend_reports_test_results.json', 'w') as f:
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