#!/usr/bin/env python3

import requests
import json
import sys
import time

# Configuration
BASE_URL = "https://category-results.preview.emergentagent.com/api"
DEALER_CREDENTIALS = {
    "email": "dealer@platform.com",
    "password": "Dealer123!"
}

class CategorySearchTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []

    def log_test(self, test_name, success, status_code, details="", response_time=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "status_code": status_code,
            "details": details,
            "response_time": response_time
        }
        self.test_results.append(result)
        status_icon = "✅" if success else "❌"
        time_info = f" ({response_time:.2f}s)" if response_time else ""
        print(f"{status_icon} {test_name}: {status_code}{time_info} - {details}")

    def test_categories_endpoint(self):
        """Test GET /api/categories?module=real_estate&country=DE"""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{BASE_URL}/categories",
                params={
                    "module": "real_estate",
                    "country": "DE"
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check that categories have required fields
                    sample_cat = data[0]
                    required_fields = ["id", "name", "slug", "parent_id"]
                    missing_fields = [f for f in required_fields if f not in sample_cat]
                    
                    if missing_fields:
                        self.log_test(
                            "GET /api/categories (real_estate)",
                            False,
                            200,
                            f"Missing required fields: {missing_fields}",
                            response_time
                        )
                        return False
                    else:
                        self.log_test(
                            "GET /api/categories (real_estate)",
                            True,
                            200,
                            f"Found {len(data)} categories with required fields (slug/name/parent_id)",
                            response_time
                        )
                        return True
                else:
                    self.log_test(
                        "GET /api/categories (real_estate)",
                        False,
                        200,
                        "Response is not a non-empty list",
                        response_time
                    )
                    return False
            else:
                self.log_test(
                    "GET /api/categories (real_estate)",
                    False,
                    response.status_code,
                    f"Error: {response.text}",
                    response_time
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "GET /api/categories (real_estate)",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_search_v2_basic(self):
        """Test GET /api/v2/search?country=DE&category=konut&page=1&limit=5"""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{BASE_URL}/v2/search",
                params={
                    "country": "DE",
                    "category": "konut",
                    "page": 1,
                    "limit": 5
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["items", "facets", "facet_meta", "pagination"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    self.log_test(
                        "GET /api/v2/search (konut basic)",
                        False,
                        200,
                        f"Missing required fields: {missing_fields}",
                        response_time
                    )
                    return False
                else:
                    pagination = data.get("pagination", {})
                    self.log_test(
                        "GET /api/v2/search (konut basic)",
                        True,
                        200,
                        f"Valid payload schema, {len(data['items'])} items, total: {pagination.get('total', 'unknown')}",
                        response_time
                    )
                    return True
            else:
                self.log_test(
                    "GET /api/v2/search (konut basic)",
                    False,
                    response.status_code,
                    f"Error: {response.text}",
                    response_time
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "GET /api/v2/search (konut basic)",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_search_v2_showcase(self):
        """Test GET /api/v2/search?country=DE&category=konut&doping_type=showcase&page=1&limit=8"""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{BASE_URL}/v2/search",
                params={
                    "country": "DE",
                    "category": "konut",
                    "doping_type": "showcase",
                    "page": 1,
                    "limit": 8
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["items", "facets", "facet_meta", "pagination"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    self.log_test(
                        "GET /api/v2/search (konut showcase)",
                        False,
                        200,
                        f"Missing required fields: {missing_fields}",
                        response_time
                    )
                    return False
                else:
                    pagination = data.get("pagination", {})
                    self.log_test(
                        "GET /api/v2/search (konut showcase)",
                        True,
                        200,
                        f"Valid payload, category-scoped showcase, {len(data['items'])} items, total: {pagination.get('total', 'unknown')}",
                        response_time
                    )
                    return True
            else:
                self.log_test(
                    "GET /api/v2/search (konut showcase)",
                    False,
                    response.status_code,
                    f"Error: {response.text}",
                    response_time
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "GET /api/v2/search (konut showcase)",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_search_v2_satilik(self):
        """Test GET /api/v2/search?country=DE&category=satilik&page=1&limit=5"""
        try:
            start_time = time.time()
            response = self.session.get(
                f"{BASE_URL}/v2/search",
                params={
                    "country": "DE",
                    "category": "satilik",
                    "page": 1,
                    "limit": 5
                },
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["items", "facets", "facet_meta", "pagination"]
                missing_fields = [f for f in required_fields if f not in data]
                
                if missing_fields:
                    self.log_test(
                        "GET /api/v2/search (satilik)",
                        False,
                        200,
                        f"Missing required fields: {missing_fields}",
                        response_time
                    )
                    return False
                else:
                    pagination = data.get("pagination", {})
                    self.log_test(
                        "GET /api/v2/search (satilik)",
                        True,
                        200,
                        f"Valid payload, {len(data['items'])} items, total: {pagination.get('total', 'unknown')}",
                        response_time
                    )
                    return True
            else:
                self.log_test(
                    "GET /api/v2/search (satilik)",
                    False,
                    response.status_code,
                    f"Error: {response.text}",
                    response_time
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "GET /api/v2/search (satilik)",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def validate_no_5xx_errors(self):
        """Validate no 5xx errors occurred in previous tests"""
        five_xx_errors = [r for r in self.test_results if isinstance(r["status_code"], int) and 500 <= r["status_code"] < 600]
        
        if five_xx_errors:
            self.log_test(
                "5xx Error Validation",
                False,
                "VALIDATION",
                f"Found {len(five_xx_errors)} 5xx errors in previous tests"
            )
            return False
        else:
            self.log_test(
                "5xx Error Validation",
                True,
                "VALIDATION",
                "No 5xx errors found in any test"
            )
            return True

    def validate_response_times(self):
        """Validate response times are reasonable (<5 seconds)"""
        slow_tests = [r for r in self.test_results if r.get("response_time") and r["response_time"] > 5.0]
        
        if slow_tests:
            slow_names = [r["test"] for r in slow_tests]
            self.log_test(
                "Response Time Validation",
                False,
                "VALIDATION",
                f"Found slow responses (>5s): {slow_names}"
            )
            return False
        else:
            avg_time = sum(r.get("response_time", 0) for r in self.test_results if r.get("response_time")) / len([r for r in self.test_results if r.get("response_time")])
            self.log_test(
                "Response Time Validation",
                True,
                "VALIDATION",
                f"All responses under 5s (avg: {avg_time:.2f}s)"
            )
            return True

    def run_category_search_tests(self):
        """Run category search template flow tests"""
        print("🔍 Starting Category Search Template Flow Tests...")
        print("=" * 60)
        
        tests = [
            self.test_categories_endpoint,
            self.test_search_v2_basic,
            self.test_search_v2_showcase,
            self.test_search_v2_satilik,
        ]
        
        all_passed = True
        for test_func in tests:
            success = test_func()
            if not success:
                all_passed = False
                
        # Validation tests
        print("\n🔍 Running Validation Tests...")
        print("-" * 60)
        
        validation_tests = [
            self.validate_no_5xx_errors,
            self.validate_response_times,
        ]
        
        for test_func in validation_tests:
            success = test_func()
            if not success:
                all_passed = False
                
        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 CATEGORY SEARCH TEMPLATE FLOW TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            time_info = f" ({result['response_time']:.2f}s)" if result.get('response_time') else ""
            print(f"{status_icon} {result['test']}: {result['status_code']}{time_info}")
            
        print(f"\n📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        if passed == total:
            print("🎉 OVERALL RESULT: PASS - All category search template flow tests working correctly")
            return True
        else:
            print("⚠️ OVERALL RESULT: FAIL - Some category search template flow tests have issues")
            return False


class DealerBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
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

    def test_dealer_login(self):
        """Test POST /api/auth/login with dealer credentials"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=DEALER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                if self.access_token:
                    # Set auth header for subsequent requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    user_email = data.get("user", {}).get("email", "Unknown")
                    self.log_test(
                        "POST /api/auth/login (dealer)",
                        True,
                        200,
                        f"Login successful, token received, user: {user_email}"
                    )
                    return True
                else:
                    self.log_test(
                        "POST /api/auth/login (dealer)",
                        False,
                        200,
                        "Response 200 but no access token in response"
                    )
                    return False
            else:
                self.log_test(
                    "POST /api/auth/login (dealer)",
                    False,
                    response.status_code,
                    f"Login failed: {response.text}"
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "POST /api/auth/login (dealer)",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_portal_config(self):
        """Test GET /api/dealer/portal/config"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/portal/config",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Portal config retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/portal/config",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/portal/config",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_navigation_summary(self):
        """Test GET /api/dealer/dashboard/navigation-summary"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/dashboard/navigation-summary",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Navigation summary retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/dashboard/navigation-summary",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/dashboard/navigation-summary",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_messages_inbox(self):
        """Test GET /api/dealer/messages?folder=inbox"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/messages",
                params={"folder": "inbox"},
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Messages inbox retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/messages?folder=inbox",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/messages?folder=inbox",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_settings_preferences(self):
        """Test GET /api/dealer/settings/preferences"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/settings/preferences",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Settings preferences retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/settings/preferences",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/settings/preferences",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def run_all_tests(self):
        """Run all dealer backend regression tests"""
        print("🚀 Starting Dealer Portal Backend Regression Tests...")
        print("=" * 60)
        
        # Step 1: Authenticate
        login_success = self.test_dealer_login()
        if not login_success:
            print("\n❌ CRITICAL: Dealer login failed. Stopping tests.")
            return False
            
        print("\n🔐 Authentication successful. Running API tests...")
        print("-" * 60)
        
        # Step 2: Test all dealer endpoints
        tests = [
            self.test_dealer_portal_config,
            self.test_dealer_navigation_summary,
            self.test_dealer_messages_inbox,
            self.test_dealer_settings_preferences
        ]
        
        all_passed = True
        for test_func in tests:
            success = test_func()
            if not success:
                all_passed = False
                
        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 DEALER PORTAL BACKEND REGRESSION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {result['test']}: {result['status_code']}")
            
        print(f"\n📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        if passed == total:
            print("🎉 OVERALL RESULT: PASS - All dealer portal endpoints working correctly")
            return True
        else:
            print("⚠️ OVERALL RESULT: FAIL - Some dealer portal endpoints have issues")
            return False

def main():
    """Main test execution function"""
    # Check if we should run category search tests or dealer tests
    if len(sys.argv) > 1 and sys.argv[1] == "category-search":
        tester = CategorySearchTester()
        
        try:
            # Run category search template flow tests
            overall_success = tester.run_category_search_tests()
            
            # Print summary
            final_result = tester.print_summary()
            
            # Exit with appropriate code
            sys.exit(0 if final_result else 1)
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n💥 Unexpected error: {str(e)}")
            sys.exit(1)
    else:
        # Default to dealer tests
        tester = DealerBackendTester()
        
        try:
            # Run all tests
            overall_success = tester.run_all_tests()
            
            # Print summary
            final_result = tester.print_summary()
            
            # Exit with appropriate code
            sys.exit(0 if final_result else 1)
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Tests interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n💥 Unexpected error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()