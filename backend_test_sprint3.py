#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

class Sprint3FinanceAPITester:
    def __init__(self, base_url="https://mongo-tasfiye.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.country_admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.failures = []
        
        # Test data storage
        self.created_invoice_id = None
        self.created_tax_rate_id = None
        self.created_plan_id = None
        self.dealer_user_id = None

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
                 data: Optional[Dict] = None, headers: Optional[Dict] = None, 
                 token: Optional[str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        # Use provided token or default admin token
        auth_token = token or self.admin_token
        if auth_token:
            request_headers['Authorization'] = f'Bearer {auth_token}'
        
        if headers:
            request_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=request_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_detail = response.json().get('detail', 'No detail')
                    details += f", Error: {error_detail}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            
            return success, response.json() if response.content else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def login_admin(self) -> bool:
        """Login as super admin"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            return True
        return False

    def login_country_admin(self) -> bool:
        """Login as country admin"""
        success, response = self.run_test(
            "Country Admin Login",
            "POST", 
            "auth/login",
            200,
            data={"email": "countryadmin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.country_admin_token = response['access_token']
            return True
        return False

    def get_dealer_user_id(self) -> bool:
        """Get a dealer user ID for testing"""
        success, response = self.run_test(
            "Get Dealers List",
            "GET",
            "admin/dealers?limit=1",
            200
        )
        if success and response.get('items'):
            self.dealer_user_id = response['items'][0]['id']
            self.log_test("Found Dealer User ID", True, f"ID: {self.dealer_user_id}")
            return True
        return False

    def test_tax_rate_crud(self) -> bool:
        """Test TaxRate CRUD operations"""
        print("\n=== Testing TaxRate CRUD ===")
        
        # Create tax rate
        tax_rate_data = {
            "country_code": "DE",
            "rate": 19.0,
            "effective_date": "2024-01-01T00:00:00Z",
            "active_flag": True
        }
        
        success, response = self.run_test(
            "Create Tax Rate",
            "POST",
            "admin/tax-rates",
            200,
            data=tax_rate_data
        )
        
        if success and response.get('tax_rate', {}).get('id'):
            self.created_tax_rate_id = response['tax_rate']['id']
        else:
            return False

        # List tax rates
        success, response = self.run_test(
            "List Tax Rates",
            "GET",
            "admin/tax-rates?country=DE",
            200
        )
        
        if not success:
            return False

        # Update tax rate
        update_data = {
            "rate": 20.0,
            "active_flag": True
        }
        
        success, response = self.run_test(
            "Update Tax Rate",
            "PATCH",
            f"admin/tax-rates/{self.created_tax_rate_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False

        # Soft delete tax rate
        success, response = self.run_test(
            "Soft Delete Tax Rate",
            "DELETE",
            f"admin/tax-rates/{self.created_tax_rate_id}",
            200
        )
        
        return success

    def test_plan_crud(self) -> bool:
        """Test Plan CRUD operations"""
        print("\n=== Testing Plan CRUD ===")
        
        # Create plan
        plan_data = {
            "name": "Test Premium Plan",
            "country_code": "DE",
            "price": 99.99,
            "currency": "EUR",
            "listing_quota": 50,
            "showcase_quota": 10,
            "active_flag": True
        }
        
        success, response = self.run_test(
            "Create Plan",
            "POST",
            "admin/plans",
            200,
            data=plan_data
        )
        
        if success and response.get('plan', {}).get('id'):
            self.created_plan_id = response['plan']['id']
        else:
            return False

        # List plans
        success, response = self.run_test(
            "List Plans",
            "GET",
            "admin/plans?country=DE",
            200
        )
        
        if not success:
            return False

        # Update plan
        update_data = {
            "name": "Updated Premium Plan",
            "price": 129.99,
            "active_flag": True
        }
        
        success, response = self.run_test(
            "Update Plan",
            "PATCH",
            f"admin/plans/{self.created_plan_id}",
            200,
            data=update_data
        )
        
        if not success:
            return False

        # Soft delete plan
        success, response = self.run_test(
            "Soft Delete Plan",
            "DELETE",
            f"admin/plans/{self.created_plan_id}",
            200
        )
        
        return success

    def test_invoice_crud(self) -> bool:
        """Test Invoice CRUD operations"""
        print("\n=== Testing Invoice CRUD ===")
        
        if not self.dealer_user_id or not self.created_plan_id:
            self.log_test("Invoice CRUD Prerequisites", False, "Missing dealer_user_id or plan_id")
            return False
        
        # Create invoice
        invoice_data = {
            "dealer_user_id": self.dealer_user_id,
            "country_code": "DE",
            "plan_id": self.created_plan_id,
            "amount_net": 1000.0,
            "tax_rate": 19.0,
            "currency": "EUR",
            "issued_at": datetime.now().isoformat()
        }
        
        success, response = self.run_test(
            "Create Invoice",
            "POST",
            "admin/invoices",
            200,
            data=invoice_data
        )
        
        if success and response.get('invoice', {}).get('id'):
            self.created_invoice_id = response['invoice']['id']
        else:
            return False

        # List invoices
        success, response = self.run_test(
            "List Invoices",
            "GET",
            f"admin/invoices?country=DE&dealer_user_id={self.dealer_user_id}",
            200
        )
        
        if not success:
            return False

        # Get specific invoice
        success, response = self.run_test(
            "Get Invoice Detail",
            "GET",
            f"admin/invoices/{self.created_invoice_id}",
            200
        )
        
        if not success:
            return False

        # Change invoice status to paid
        status_data = {
            "target_status": "paid",
            "note": "Payment received via test"
        }
        
        success, response = self.run_test(
            "Change Invoice Status to Paid",
            "POST",
            f"admin/invoices/{self.created_invoice_id}/status",
            200,
            data=status_data
        )
        
        if not success:
            return False

        # Create another invoice for cancelled test
        invoice_data_2 = {
            "dealer_user_id": self.dealer_user_id,
            "country_code": "DE",
            "plan_id": self.created_plan_id,
            "amount_net": 500.0,
            "tax_rate": 19.0,
            "currency": "EUR",
            "issued_at": datetime.now().isoformat()
        }
        
        success, response = self.run_test(
            "Create Second Invoice for Cancel Test",
            "POST",
            "admin/invoices",
            200,
            data=invoice_data_2
        )
        
        if not success or not response.get('invoice', {}).get('id'):
            return False
        
        second_invoice_id = response['invoice']['id']

        # Change second invoice status to cancelled
        status_data = {
            "target_status": "cancelled",
            "note": "Cancelled for testing"
        }
        
        success, response = self.run_test(
            "Change Invoice Status to Cancelled",
            "POST",
            f"admin/invoices/{second_invoice_id}/status",
            200,
            data=status_data
        )
        
        return success

    def test_revenue_endpoint(self) -> bool:
        """Test revenue calculation endpoint"""
        print("\n=== Testing Revenue Endpoint ===")
        
        # Test revenue endpoint with date range
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()
        
        success, response = self.run_test(
            "Get Revenue Report",
            "GET",
            f"admin/finance/revenue?country=DE&start_date={start_date}&end_date={end_date}",
            200
        )
        
        if success and 'total_gross' in response:
            self.log_test("Revenue Response Format", True, f"Total gross: {response.get('total_gross')}")
            return True
        else:
            self.log_test("Revenue Response Format", False, "Missing total_gross field")
            return False

    def test_dealer_detail_finance_integration(self) -> bool:
        """Test dealer detail shows finance information"""
        print("\n=== Testing Dealer Detail Finance Integration ===")
        
        if not self.dealer_user_id:
            return False
        
        success, response = self.run_test(
            "Get Dealer Detail with Finance Info",
            "GET",
            f"admin/dealers/{self.dealer_user_id}?country=DE",
            200
        )
        
        if success:
            # Check for required finance fields
            has_active_plan = 'active_plan' in response
            has_last_invoice = 'last_invoice' in response
            has_unpaid_count = 'unpaid_count' in response
            
            all_fields_present = has_active_plan and has_last_invoice and has_unpaid_count
            
            self.log_test(
                "Dealer Detail Finance Fields",
                all_fields_present,
                f"active_plan: {has_active_plan}, last_invoice: {has_last_invoice}, unpaid_count: {has_unpaid_count}"
            )
            
            return all_fields_present
        
        return False

    def test_plan_assignment(self) -> bool:
        """Test plan assignment to dealer"""
        print("\n=== Testing Plan Assignment ===")
        
        if not self.dealer_user_id or not self.created_plan_id:
            return False
        
        assignment_data = {
            "plan_id": self.created_plan_id
        }
        
        success, response = self.run_test(
            "Assign Plan to Dealer",
            "POST",
            f"admin/dealers/{self.dealer_user_id}/plan?country=DE",
            200,
            data=assignment_data
        )
        
        return success

    def test_country_scope_violations(self) -> bool:
        """Test country scope enforcement with country admin"""
        print("\n=== Testing Country Scope Violations ===")
        
        if not self.country_admin_token:
            self.log_test("Country Admin Token", False, "Country admin login failed")
            return False
        
        # Try to access FR data with DE-scoped country admin (should fail)
        success, response = self.run_test(
            "Country Scope Violation - Invoice List",
            "GET",
            "admin/invoices?country=FR",
            403,
            token=self.country_admin_token
        )
        
        if not success:
            return False
        
        # Try to access FR data with tax rates (should fail)
        success, response = self.run_test(
            "Country Scope Violation - Tax Rates",
            "GET",
            "admin/tax-rates?country=FR",
            403,
            token=self.country_admin_token
        )
        
        if not success:
            return False
        
        # Try to access FR data with plans (should fail)
        success, response = self.run_test(
            "Country Scope Violation - Plans",
            "GET",
            "admin/plans?country=FR",
            403,
            token=self.country_admin_token
        )
        
        return success

    def test_audit_logs(self) -> bool:
        """Test audit log creation for finance operations"""
        print("\n=== Testing Audit Logs ===")
        
        # Check for INVOICE_STATUS_CHANGE audit logs
        success, response = self.run_test(
            "Check Invoice Status Change Audit",
            "GET",
            "audit-logs?event_type=INVOICE_STATUS_CHANGE&resource_type=invoice",
            200
        )
        
        if not success:
            return False
        
        # Check for TAX_RATE_CHANGE audit logs
        success, response = self.run_test(
            "Check Tax Rate Change Audit",
            "GET",
            "audit-logs?event_type=TAX_RATE_CHANGE&resource_type=tax_rate",
            200
        )
        
        if not success:
            return False
        
        # Check for PLAN_CHANGE audit logs
        success, response = self.run_test(
            "Check Plan Change Audit",
            "GET",
            "audit-logs?event_type=PLAN_CHANGE&resource_type=plan",
            200
        )
        
        if not success:
            return False
        
        # Check for ADMIN_PLAN_ASSIGNMENT audit logs
        success, response = self.run_test(
            "Check Plan Assignment Audit",
            "GET",
            "audit-logs?event_type=ADMIN_PLAN_ASSIGNMENT",
            200
        )
        
        return success

    def save_results(self):
        """Save test results to file"""
        results = {
            "test_run_timestamp": datetime.now().isoformat(),
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(self.failures),
            "success_rate": f"{(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%",
            "test_results": self.test_results,
            "failures": self.failures,
            "test_data": {
                "created_invoice_id": self.created_invoice_id,
                "created_tax_rate_id": self.created_tax_rate_id,
                "created_plan_id": self.created_plan_id,
                "dealer_user_id": self.dealer_user_id
            }
        }
        
        with open('/app/test_reports/sprint3_backend_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📊 Test Results Summary:")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failures)}")
        print(f"Success Rate: {results['success_rate']}")
        
        if self.failures:
            print(f"\n❌ Failed Tests:")
            for failure in self.failures:
                print(f"  - {failure['test']}: {failure['details']}")

def main():
    print("🚀 Starting Sprint 3 Finance Domain API Testing...")
    
    tester = Sprint3FinanceAPITester()
    
    # Login as admin
    if not tester.login_admin():
        print("❌ Admin login failed, stopping tests")
        return 1
    
    # Login as country admin
    if not tester.login_country_admin():
        print("⚠️ Country admin login failed, skipping country scope tests")
    
    # Get dealer user ID for testing
    if not tester.get_dealer_user_id():
        print("❌ Could not find dealer user, stopping tests")
        return 1
    
    # Run all test suites
    test_suites = [
        tester.test_tax_rate_crud,
        tester.test_plan_crud,
        tester.test_invoice_crud,
        tester.test_revenue_endpoint,
        tester.test_dealer_detail_finance_integration,
        tester.test_plan_assignment,
        tester.test_country_scope_violations,
        tester.test_audit_logs
    ]
    
    for test_suite in test_suites:
        try:
            test_suite()
        except Exception as e:
            print(f"❌ Test suite failed with exception: {e}")
    
    # Save results
    tester.save_results()
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())