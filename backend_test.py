#!/usr/bin/env python3

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://category-results.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        
    def log_test(self, test_name, status, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()

    def admin_login(self):
        """Authenticate as admin and get access token"""
        print("🔐 Authenticating as admin...")
        
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.access_token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
                    self.log_test("Admin Authentication", "PASS", {
                        "email": data.get("email", "unknown"),
                        "token_length": len(self.access_token)
                    })
                    return True
                else:
                    self.log_test("Admin Authentication", "FAIL", {
                        "error": "No access_token in response",
                        "response": data
                    })
                    return False
            else:
                self.log_test("Admin Authentication", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
        except Exception as e:
            self.log_test("Admin Authentication", "FAIL", {"error": str(e)})
            return False

    def test_bindings_active(self):
        """Test GET /api/admin/site/content-layout/bindings/active with sample parameters"""
        try:
            # Test with sample parameters - this may return empty but should not error
            params = {
                "country": "DE",
                "module": "real_estate",
                "category_id": "12345678-1234-5678-9012-123456789012"  # Sample UUID
            }
            response = self.session.get(f"{BASE_URL}/admin/site/content-layout/bindings/active", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /bindings/active", "PASS", {
                    "status_code": response.status_code,
                    "response_has_data": bool(data),
                    "response_type": type(data).__name__
                })
                return data
            elif response.status_code == 404:
                # No binding found is acceptable
                self.log_test("GET /bindings/active", "PASS", {
                    "status_code": response.status_code,
                    "note": "No active binding found (acceptable)"
                })
                return None
            else:
                self.log_test("GET /bindings/active", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                })
                return None
        except Exception as e:
            self.log_test("GET /bindings/active", "FAIL", {"error": str(e)})
            return None

    def test_bindings_unbind(self):
        """Test POST /api/admin/site/content-layout/bindings/unbind"""
        try:
            # Test with sample parameters - this will likely return 404 but should not 5xx
            unbind_data = {
                "country": "DE",
                "module": "real_estate",
                "category_id": "12345678-1234-5678-9012-123456789012"  # Sample UUID
            }
            response = self.session.post(f"{BASE_URL}/admin/site/content-layout/bindings/unbind", json=unbind_data)
            
            if response.status_code in [200, 204]:
                self.log_test("POST /bindings/unbind", "PASS", {
                    "status_code": response.status_code,
                    "note": "Unbind successful"
                })
                return True
            elif response.status_code == 404:
                # No binding to unbind is acceptable
                self.log_test("POST /bindings/unbind", "PASS", {
                    "status_code": response.status_code,
                    "note": "No binding to unbind (acceptable)"
                })
                return True
            else:
                self.log_test("POST /bindings/unbind", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                })
                return False
        except Exception as e:
            self.log_test("POST /bindings/unbind", "FAIL", {"error": str(e)})
            return False

    def test_resolve_home(self):
        """Test GET /api/site/content-layout/resolve for home page"""
        try:
            # Test resolve for home page
            params = {
                "page_type": "home",
                "country": "DE",
                "module": "global"
            }
            response = self.session.get(f"{BASE_URL}/site/content-layout/resolve", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/site/content-layout/resolve (home)", "PASS", {
                    "status_code": response.status_code,
                    "page_type": data.get("page_type", "unknown"),
                    "source": data.get("source", "unknown"),
                    "has_layout": "layout" in data
                })
                return data
            else:
                self.log_test("GET /api/site/content-layout/resolve (home)", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                })
                return None
        except Exception as e:
            self.log_test("GET /api/site/content-layout/resolve (home)", "FAIL", {"error": str(e)})
            return None

    def test_resolve_search_l1(self):
        """Test GET /api/site/content-layout/resolve for search_l1"""
        try:
            # Test resolve for search L1 page
            params = {
                "page_type": "search_l1",
                "country": "DE",
                "module": "real_estate",
                "category_id": "12345678-1234-5678-9012-123456789012"  # Sample UUID
            }
            response = self.session.get(f"{BASE_URL}/site/content-layout/resolve", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/site/content-layout/resolve (search_l1)", "PASS", {
                    "status_code": response.status_code,
                    "page_type": data.get("page_type", "unknown"),
                    "source": data.get("source", "unknown"),
                    "has_layout": "layout" in data
                })
                return data
            else:
                self.log_test("GET /api/site/content-layout/resolve (search_l1)", "FAIL", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                })
                return None
        except Exception as e:
            self.log_test("GET /api/site/content-layout/resolve (search_l1)", "FAIL", {"error": str(e)})
            return None

    def test_5xx_errors(self):
        """Check for any 5xx errors in the tested flows"""
        print("🔍 Checking for 5xx errors in tested endpoints...")
        
        error_count = 0
        for result in self.test_results:
            if result["status"] == "FAIL" and "status_code" in result["details"]:
                status_code = result["details"]["status_code"]
                if 500 <= status_code < 600:
                    error_count += 1
                    print(f"   ❌ 5xx Error found: {result['test']} returned {status_code}")
        
        if error_count == 0:
            self.log_test("5xx Error Check", "PASS", {
                "total_tests": len(self.test_results),
                "5xx_errors": error_count
            })
        else:
            self.log_test("5xx Error Check", "FAIL", {
                "total_tests": len(self.test_results),
                "5xx_errors": error_count
            })

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend Sanity Test - P1.1/P1.2/P2 Continuation")
        print("=" * 70)
        
        # Step 1: Admin Login
        if not self.admin_login():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Test bindings endpoints (Note: No general /bindings endpoint exists)
        self.test_bindings_active()
        self.test_bindings_unbind()
        
        # Step 3: Test resolve endpoints
        self.test_resolve_home()
        self.test_resolve_search_l1()
        
        # Step 4: Check for 5xx errors
        self.test_5xx_errors()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r["status"] == "SKIPPED"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Skipped: {skipped_tests}")
        
        if failed_tests == 0:
            print(f"\n✅ OVERALL RESULT: PASS ({passed_tests}/{total_tests} tests passed)")
        else:
            print(f"\n❌ OVERALL RESULT: FAIL ({passed_tests}/{total_tests} tests passed)")
        
        # Print failed tests details
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  ❌ {result['test']}")
                    if "error" in result["details"]:
                        print(f"     Error: {result['details']['error']}")
                    if "status_code" in result["details"]:
                        print(f"     Status Code: {result['details']['status_code']}")
        
        print("\n" + "=" * 70)

def main():
    """Main function"""
    tester = BackendTester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        # Return appropriate exit code
        failed_tests = len([r for r in tester.test_results if r["status"] == "FAIL"])
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()