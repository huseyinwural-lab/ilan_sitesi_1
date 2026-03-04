#!/usr/bin/env python3

import requests
import json
import sys
import time

# Configuration
BASE_URL = "https://category-results.preview.emergentagent.com/api"

class FAZ2RegressionTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name, success, status_code, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "status_code": status_code,
            "details": details
        }
        self.test_results.append(result)
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}: {status_code} - {details}")
        return success

    def test_health_endpoint(self):
        """Test GET /api/health"""
        try:
            response = self.session.get(f"{BASE_URL}/health", timeout=10)
            
            if response.status_code in [200, 503]:
                # Both 200 and 503 are acceptable for health checks
                try:
                    data = response.json()
                    success = True
                    details = f"Health endpoint responding, data keys: {list(data.keys()) if data else 'empty'}"
                except json.JSONDecodeError:
                    success = False
                    details = "Invalid JSON response"
            else:
                success = False
                details = f"Unexpected status code: {response.status_code}"
                
            return self.log_test("GET /api/health", success, response.status_code, details)
            
        except requests.RequestException as e:
            return self.log_test("GET /api/health", False, "ERROR", f"Request exception: {str(e)}")

    def test_health_search_endpoint(self):
        """Test GET /api/health/search (200/503 deterministik)"""
        try:
            response = self.session.get(f"{BASE_URL}/health/search", timeout=10)
            
            # Should return 200 or 503 deterministically
            if response.status_code in [200, 503]:
                try:
                    data = response.json()
                    success = True
                    
                    # Check for required fields in degraded response
                    if response.status_code == 503:
                        has_error_code = "error_code" in data
                        has_degraded = "degraded" in data  
                        has_retry_after = "retry_after_seconds" in data
                        
                        details = f"Degraded response - error_code: {has_error_code}, degraded: {has_degraded}, retry_after_seconds: {has_retry_after}"
                        
                        # Verify Meili degraded payload fields
                        if not (has_error_code and has_degraded and has_retry_after):
                            success = False
                            details += " - Missing required degraded payload fields"
                    else:
                        details = f"Healthy response - healthy: {data.get('healthy')}, degraded: {data.get('degraded')}"
                        
                except json.JSONDecodeError:
                    success = False
                    details = "Invalid JSON response"
            else:
                success = False
                details = f"Non-deterministic status code: {response.status_code} (expected 200 or 503)"
                
            return self.log_test("GET /api/health/search", success, response.status_code, details)
            
        except requests.RequestException as e:
            return self.log_test("GET /api/health/search", False, "ERROR", f"Request exception: {str(e)}")

    def test_v2_search_endpoint(self):
        """Test GET /api/v2/search?country=DE&size=2&page=1"""
        try:
            params = {
                "country": "DE",
                "size": "2", 
                "page": "1"
            }
            response = self.session.get(f"{BASE_URL}/v2/search", params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    success = True
                    
                    # Check response structure
                    has_results = "results" in data or "data" in data or "listings" in data
                    total_count = data.get("total", 0) if isinstance(data, dict) else 0
                    
                    details = f"Search successful - has_results: {has_results}, total: {total_count}"
                    
                except json.JSONDecodeError:
                    success = False
                    details = "Invalid JSON response"
            elif response.status_code in [503]:
                # Search might be degraded
                success = True
                details = "Search service degraded (503) - acceptable"
            else:
                success = False
                details = f"Search failed with status {response.status_code}"
                
            return self.log_test("GET /api/v2/search?country=DE&size=2&page=1", success, response.status_code, details)
            
        except requests.RequestException as e:
            return self.log_test("GET /api/v2/search", False, "ERROR", f"Request exception: {str(e)}")

    def test_admin_users_unauthorized(self):
        """Test GET /api/admin/users authsuz (401/403/404 deterministik json)"""
        try:
            # Make request without authentication
            response = self.session.get(f"{BASE_URL}/admin/users", timeout=10)
            
            # Should return 401, 403, or 404 deterministically
            if response.status_code in [401, 403, 404]:
                try:
                    data = response.json()
                    success = True
                    
                    # Verify it returns JSON with error details
                    has_detail = "detail" in data or "message" in data or "error" in data
                    details = f"Properly blocked unauthorized access - JSON response: {has_detail}"
                    
                    if not has_detail:
                        details += " - WARNING: No error detail in JSON"
                        
                except json.JSONDecodeError:
                    success = False
                    details = "Non-JSON response (should be JSON)"
            else:
                success = False
                details = f"Unexpected status code: {response.status_code} (expected 401/403/404)"
                
            return self.log_test("GET /api/admin/users (unauthorized)", success, response.status_code, details)
            
        except requests.RequestException as e:
            return self.log_test("GET /api/admin/users (unauthorized)", False, "ERROR", f"Request exception: {str(e)}")

    def test_meili_degraded_payload_fields(self):
        """Additional test for Meili degrade payload fields"""
        try:
            # Test health/search endpoint multiple times to catch degraded states
            for attempt in range(3):
                response = self.session.get(f"{BASE_URL}/health/search", timeout=5)
                
                if response.status_code == 503:
                    try:
                        data = response.json()
                        
                        # Check all required degraded payload fields
                        required_fields = ["error_code", "degraded", "retry_after_seconds"]
                        present_fields = [field for field in required_fields if field in data]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if len(present_fields) == len(required_fields):
                            success = True
                            details = f"All required degraded fields present: {required_fields}"
                        else:
                            success = False
                            details = f"Missing degraded fields: {missing_fields}, present: {present_fields}"
                            
                        return self.log_test("Meili degraded payload validation", success, 503, details)
                        
                    except json.JSONDecodeError:
                        success = False
                        details = "Invalid JSON in degraded response"
                        return self.log_test("Meili degraded payload validation", success, 503, details)
                        
                time.sleep(0.5)  # Short delay between attempts
                
            # If no degraded state found, that's also acceptable
            return self.log_test("Meili degraded payload validation", True, "N/A", "No degraded state encountered (healthy service)")
            
        except requests.RequestException as e:
            return self.log_test("Meili degraded payload validation", False, "ERROR", f"Request exception: {str(e)}")

    def run_all_tests(self):
        """Run all FAZ 2 regression tests"""
        print("🚀 Starting FAZ 2 Backend Regression Tests...")
        print("=" * 60)
        
        tests = [
            ("Basic Health Check", self.test_health_endpoint),
            ("Search Health Check", self.test_health_search_endpoint), 
            ("V2 Search Endpoint", self.test_v2_search_endpoint),
            ("Admin Users Unauthorized", self.test_admin_users_unauthorized),
            ("Meili Degraded Payload", self.test_meili_degraded_payload_fields)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            print("-" * 40)
            success = test_func()
            if not success:
                all_passed = False
                
        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 FAZ 2 BACKEND REGRESSION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {result['test']}: {result['status_code']} - {result['details']}")
            
        print(f"\n📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        if passed == total:
            print("🎉 OVERALL RESULT: PASS - All FAZ 2 regression tests successful")
            return "PASS"
        else:
            print("⚠️ OVERALL RESULT: FAIL - Some FAZ 2 regression tests failed")
            return "FAIL"

def main():
    """Main test execution function"""
    tester = FAZ2RegressionTester()
    
    try:
        # Run all tests
        overall_success = tester.run_all_tests()
        
        # Print summary
        final_result = tester.print_summary()
        
        # Short PASS/FAIL response as requested
        print(f"\n🏁 Kısa PASS/FAIL: {final_result}")
        
        # Exit with appropriate code
        sys.exit(0 if final_result == "PASS" else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()