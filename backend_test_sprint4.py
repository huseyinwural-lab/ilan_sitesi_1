#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

class Sprint4APITester:
    def __init__(self, base_url="https://corporate-ui-build.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.country_admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.failures = []
        self.created_resources = {
            'countries': [],
            'system_settings': []
        }

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
                 use_country_admin: bool = False) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        request_headers = {'Content-Type': 'application/json'}
        
        # Use appropriate token
        token = self.country_admin_token if use_country_admin else self.admin_token
        if token:
            request_headers['Authorization'] = f'Bearer {token}'
        
        if headers:
            request_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=request_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=request_headers, timeout=30)
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
        """Login as super admin user"""
        success, response = self.run_test(
            "Admin Login (super_admin)",
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
        """Login as country admin user (DE scope)"""
        success, response = self.run_test(
            "Country Admin Login (DE scope)",
            "POST", 
            "auth/login",
            200,
            data={"email": "countryadmin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.country_admin_token = response['access_token']
            return True
        return False

    def test_country_crud_operations(self):
        """Test Country CRUD endpoints + audit"""
        print("\n🔍 Testing Country CRUD Operations")
        
        # Test GET /api/admin/countries (list)
        success, countries_data = self.run_test(
            "List Countries",
            "GET",
            "admin/countries",
            200
        )
        
        if not success:
            return False

        # Test POST /api/admin/countries (create)
        test_country = {
            "country_code": "TR",
            "name": "Turkey Test",
            "default_currency": "TRY",
            "default_language": "tr",
            "active_flag": True
        }
        
        success, create_response = self.run_test(
            "Create Country (TR)",
            "POST",
            "admin/countries",
            201,
            data=test_country
        )
        
        if success:
            self.created_resources['countries'].append("TR")

        # Test PATCH /api/admin/countries/{country_code} (update)
        update_data = {
            "name": "Turkey Updated",
            "default_currency": "TRY",
            "active_flag": True
        }
        
        success, update_response = self.run_test(
            "Update Country (TR)",
            "PATCH",
            "admin/countries/TR",
            200,
            data=update_data
        )

        # Test DELETE /api/admin/countries/{country_code} (soft delete)
        success, delete_response = self.run_test(
            "Delete Country (TR)",
            "DELETE",
            "admin/countries/TR",
            200
        )

        return True

    def test_system_settings_crud_operations(self):
        """Test System Settings CRUD endpoints + audit"""
        print("\n🔍 Testing System Settings CRUD Operations")
        
        # Test GET /api/admin/system-settings (list)
        success, settings_data = self.run_test(
            "List System Settings",
            "GET",
            "admin/system-settings",
            200
        )
        
        if not success:
            return False

        # Test POST /api/admin/system-settings (create global setting)
        global_setting = {
            "key": "billing.vat_rate_default",
            "value": 19,
            "description": "Default VAT rate for billing"
        }
        
        success, create_response = self.run_test(
            "Create Global System Setting",
            "POST",
            "admin/system-settings",
            201,
            data=global_setting
        )
        
        if success and 'id' in create_response:
            self.created_resources['system_settings'].append(create_response['id'])

        # Test POST /api/admin/system-settings (create country-specific setting)
        country_setting = {
            "key": "billing.vat_rate_default",
            "value": 20,
            "country_code": "DE",
            "description": "Germany-specific VAT rate"
        }
        
        success, create_response = self.run_test(
            "Create Country-Specific System Setting (DE)",
            "POST",
            "admin/system-settings",
            201,
            data=country_setting
        )
        
        if success and 'id' in create_response:
            self.created_resources['system_settings'].append(create_response['id'])

        # Test PATCH /api/admin/system-settings/{id} (update)
        if self.created_resources['system_settings']:
            setting_id = self.created_resources['system_settings'][0]
            update_data = {
                "value": 21,
                "description": "Updated VAT rate"
            }
            
            success, update_response = self.run_test(
                "Update System Setting",
                "PATCH",
                f"admin/system-settings/{setting_id}",
                200,
                data=update_data
            )

        return True

    def test_system_settings_effective_view(self):
        """Test System Settings Effective View"""
        print("\n🔍 Testing System Settings Effective View")
        
        # Test GET /api/system-settings/effective (global)
        success, global_effective = self.run_test(
            "Get Effective Settings (Global)",
            "GET",
            "system-settings/effective",
            200
        )
        
        # Test GET /api/system-settings/effective?country=DE (country-specific)
        success, de_effective = self.run_test(
            "Get Effective Settings (DE)",
            "GET",
            "system-settings/effective?country=DE",
            200
        )
        
        # Test GET /api/system-settings/effective?country=FR (different country)
        success, fr_effective = self.run_test(
            "Get Effective Settings (FR)",
            "GET",
            "system-settings/effective?country=FR",
            200
        )

        return True

    def test_dashboard_kpi_endpoints(self):
        """Test Dashboard KPI endpoints"""
        print("\n🔍 Testing Dashboard KPI Endpoints")
        
        # Test GET /api/admin/dashboard/summary?country=DE
        success, de_summary = self.run_test(
            "Dashboard Summary (DE)",
            "GET",
            "admin/dashboard/summary?country=DE",
            200
        )
        
        if success:
            # Verify KPI structure
            expected_fields = ['total_listings', 'published_listings', 'pending_moderation', 'active_dealers', 'revenue_mtd']
            missing_fields = [field for field in expected_fields if field not in de_summary]
            if missing_fields:
                self.log_test("Dashboard Summary KPI Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard Summary KPI Structure", True, "All expected KPI fields present")

        # Test GET /api/admin/dashboard/country-compare
        success, country_compare = self.run_test(
            "Dashboard Country Compare",
            "GET",
            "admin/dashboard/country-compare",
            200
        )
        
        if success:
            # Verify country compare structure
            if 'items' in country_compare and isinstance(country_compare['items'], list):
                self.log_test("Country Compare Structure", True, f"Found {len(country_compare['items'])} countries")
            else:
                self.log_test("Country Compare Structure", False, "Missing or invalid items array")

        return True

    def test_country_scope_violations(self):
        """Test Country-scope violation returns 403"""
        print("\n🔍 Testing Country-Scope Violations")
        
        if not self.country_admin_token:
            self.log_test("Country Scope Test Setup", False, "Country admin token not available")
            return False

        # Test country admin accessing unauthorized country (FR) - should return 403
        success, response = self.run_test(
            "Country Scope Violation - Dashboard Summary (FR)",
            "GET",
            "admin/dashboard/summary?country=FR",
            403,
            use_country_admin=True
        )

        # Test country admin accessing authorized country (DE) - should return 200
        success, response = self.run_test(
            "Country Scope Authorized - Dashboard Summary (DE)",
            "GET",
            "admin/dashboard/summary?country=DE",
            200,
            use_country_admin=True
        )

        # Test country admin accessing countries endpoint with FR scope - should return 403
        success, response = self.run_test(
            "Country Scope Violation - Countries (FR)",
            "GET",
            "admin/countries?country=FR",
            403,
            use_country_admin=True
        )

        return True

    def test_audit_logs_creation(self):
        """Test that audit logs are created for CRUD operations"""
        print("\n🔍 Testing Audit Logs Creation")
        
        # Test GET /api/audit-logs with filters for recent events
        success, audit_logs = self.run_test(
            "Get Recent Audit Logs",
            "GET",
            "audit-logs?limit=50",
            200
        )
        
        if success and isinstance(audit_logs, list):
            # Look for COUNTRY_CHANGE events
            country_events = [log for log in audit_logs if log.get('event_type') == 'COUNTRY_CHANGE']
            if country_events:
                self.log_test("Country Change Audit Logs", True, f"Found {len(country_events)} COUNTRY_CHANGE events")
            else:
                self.log_test("Country Change Audit Logs", False, "No COUNTRY_CHANGE audit events found")
            
            # Look for SYSTEM_SETTING_CHANGE events
            setting_events = [log for log in audit_logs if log.get('event_type') == 'SYSTEM_SETTING_CHANGE']
            if setting_events:
                self.log_test("System Setting Change Audit Logs", True, f"Found {len(setting_events)} SYSTEM_SETTING_CHANGE events")
            else:
                self.log_test("System Setting Change Audit Logs", False, "No SYSTEM_SETTING_CHANGE audit events found")

        return True

    def run_all_tests(self):
        """Run all Sprint 4 tests"""
        print("🚀 Starting Sprint 4 API Testing")
        print("=" * 60)
        
        # Login tests
        if not self.login_admin():
            print("❌ Admin login failed, stopping tests")
            return False
            
        if not self.login_country_admin():
            print("❌ Country admin login failed, continuing with limited tests")

        # Core functionality tests
        self.test_country_crud_operations()
        self.test_system_settings_crud_operations()
        self.test_system_settings_effective_view()
        self.test_dashboard_kpi_endpoints()
        
        # Security tests
        if self.country_admin_token:
            self.test_country_scope_violations()
        
        # Audit tests
        self.test_audit_logs_creation()

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failures:
            print(f"\n❌ Failed Tests ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  - {failure['test']}: {failure['details']}")
        
        # Save detailed results
        results = {
            "summary": f"Sprint 4 API Testing - {self.tests_passed}/{self.tests_run} tests passed",
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": len(self.failures),
            "test_results": self.test_results,
            "failures": self.failures,
            "created_resources": self.created_resources
        }
        
        with open('/app/test_reports/sprint4_backend_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/test_reports/sprint4_backend_test_results.json")
        
        return self.tests_passed == self.tests_run

def main():
    tester = Sprint4APITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())