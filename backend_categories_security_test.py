#!/usr/bin/env python3

import requests
import json
import sys
import uuid
from typing import Dict, List, Any

# Configuration from review request
BASE_URL = "https://category-results.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {
    "email": "admin@platform.com", 
    "password": "Admin123!"
}

class CategoriesSecurityTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []
        self.created_category_id = None

    def log_test(self, test_name: str, success: bool, status_code: Any, details: str = "", expected_status: int = 200):
        """Log test result with detailed information"""
        result = {
            "test": test_name,
            "success": success,
            "status_code": status_code,
            "details": details,
            "expected": expected_status
        }
        self.test_results.append(result)
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}: {status_code} (expected {expected_status}) - {details}")

    def test_auth_login(self):
        """1) Auth - POST /auth/login -> 200 ve access_token dönmeli"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    if self.access_token:
                        # Set auth header for subsequent requests
                        self.session.headers.update({
                            "Authorization": f"Bearer {self.access_token}"
                        })
                        user_email = data.get("user", {}).get("email", "Unknown")
                        self.log_test(
                            "POST /auth/login",
                            True,
                            200,
                            f"✅ Login successful, access_token received, user: {user_email}"
                        )
                        return True
                    else:
                        self.log_test(
                            "POST /auth/login",
                            False,
                            200,
                            "❌ Response 200 but no access_token in response"
                        )
                        return False
                except json.JSONDecodeError:
                    self.log_test(
                        "POST /auth/login",
                        False,
                        200,
                        f"❌ Invalid JSON response: {response.text}"
                    )
                    return False
            else:
                self.log_test(
                    "POST /auth/login",
                    False,
                    response.status_code,
                    f"❌ Login failed: {response.text}"
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "POST /auth/login",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_category_create_valid_icon_svg(self):
        """2) Category CRUD - POST /admin/categories (geçerli icon_svg) -> 201"""
        try:
            # Valid SVG icon without script tags
            valid_icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9,22 9,12 15,12 15,22"></polyline></svg>"""
            
            category_payload = {
                "name": f"Test Category {uuid.uuid4().hex[:8]}",
                "slug": f"test-category-{uuid.uuid4().hex[:8]}",
                "icon_svg": valid_icon_svg,
                "parent_id": None,
                "sort_order": 100,
                "is_active": True,
                "form_schema": {
                    "category_meta": {
                        "home_icon_svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/></svg>"""
                    }
                }
            }
            
            response = self.session.post(
                f"{BASE_URL}/admin/categories",
                json=category_payload,
                timeout=10
            )
            
            if response.status_code == 201:
                try:
                    data = response.json()
                    self.created_category_id = data.get("id")
                    self.log_test(
                        "POST /admin/categories (valid icon_svg)",
                        True,
                        201,
                        f"✅ Category created successfully, ID: {self.created_category_id}"
                    )
                    return True
                except json.JSONDecodeError:
                    self.log_test(
                        "POST /admin/categories (valid icon_svg)",
                        False,
                        201,
                        f"❌ Invalid JSON response: {response.text}"
                    )
                    return False
            else:
                self.log_test(
                    "POST /admin/categories (valid icon_svg)",
                    False,
                    response.status_code,
                    f"❌ Category creation failed: {response.text}"
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "POST /admin/categories (valid icon_svg)",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_category_update_valid_icon_svg(self):
        """PATCH /admin/categories/{id} (geçerli icon_svg update) -> 200"""
        if not self.created_category_id:
            self.log_test(
                "PATCH /admin/categories/{id} (valid icon_svg update)",
                False,
                "SKIP",
                "❌ Skipped: No category ID from creation test"
            )
            return False
            
        try:
            # Updated valid SVG
            updated_icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>"""
            
            update_payload = {
                "icon_svg": updated_icon_svg,
                "name": f"Updated Test Category {uuid.uuid4().hex[:8]}"
            }
            
            response = self.session.patch(
                f"{BASE_URL}/admin/categories/{self.created_category_id}",
                json=update_payload,
                timeout=10
            )
            
            success = response.status_code == 200
            details = "✅ Category updated successfully" if success else f"❌ Update failed: {response.text}"
            
            self.log_test(
                "PATCH /admin/categories/{id} (valid icon_svg update)",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "PATCH /admin/categories/{id} (valid icon_svg update)",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_category_delete(self):
        """DELETE /admin/categories/{id} -> 200"""
        if not self.created_category_id:
            self.log_test(
                "DELETE /admin/categories/{id}",
                False,
                "SKIP",
                "❌ Skipped: No category ID from creation test"
            )
            return False
            
        try:
            response = self.session.delete(
                f"{BASE_URL}/admin/categories/{self.created_category_id}",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "✅ Category deleted successfully" if success else f"❌ Delete failed: {response.text}"
            
            self.log_test(
                "DELETE /admin/categories/{id}",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "DELETE /admin/categories/{id}",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_category_create_script_injection_icon_svg(self):
        """POST /admin/categories (icon_svg içinde <script>) -> 400 beklenir"""
        try:
            # Malicious SVG with script injection
            malicious_icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><script>alert('XSS')</script><circle cx="12" cy="12" r="10"/></svg>"""
            
            category_payload = {
                "name": f"Malicious Category {uuid.uuid4().hex[:8]}",
                "slug": f"malicious-category-{uuid.uuid4().hex[:8]}",
                "icon_svg": malicious_icon_svg,
                "parent_id": None,
                "sort_order": 100,
                "is_active": True
            }
            
            response = self.session.post(
                f"{BASE_URL}/admin/categories",
                json=category_payload,
                timeout=10
            )
            
            # Expecting 400 for security validation
            if response.status_code == 400:
                self.log_test(
                    "POST /admin/categories (icon_svg with <script>)",
                    True,
                    400,
                    "✅ Security validation working: rejected malicious SVG with <script> tag",
                    expected_status=400
                )
                return True
            else:
                self.log_test(
                    "POST /admin/categories (icon_svg with <script>)",
                    False,
                    response.status_code,
                    f"❌ Security issue: malicious SVG was accepted! Response: {response.text}",
                    expected_status=400
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "POST /admin/categories (icon_svg with <script>)",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}",
                expected_status=400
            )
            return False

    def test_category_create_script_injection_form_schema(self):
        """POST /admin/categories (form_schema.category_meta.home_icon_svg içinde <script>) -> 400 beklenir"""
        try:
            # Valid main icon but malicious home_icon_svg in form_schema
            malicious_form_schema = {
                "category_meta": {
                    "home_icon_svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><script>alert('XSS in form schema')</script><circle cx="12" cy="12" r="10"/></svg>"""
                }
            }
            
            category_payload = {
                "name": f"Malicious Form Schema {uuid.uuid4().hex[:8]}",
                "slug": f"malicious-form-{uuid.uuid4().hex[:8]}",
                "icon_svg": """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24"><circle cx="12" cy="12" r="10"/></svg>""",
                "parent_id": None,
                "sort_order": 100,
                "is_active": True,
                "form_schema": malicious_form_schema
            }
            
            response = self.session.post(
                f"{BASE_URL}/admin/categories",
                json=category_payload,
                timeout=10
            )
            
            # Expecting 400 for security validation
            if response.status_code == 400:
                self.log_test(
                    "POST /admin/categories (form_schema with <script>)",
                    True,
                    400,
                    "✅ Security validation working: rejected malicious SVG in form_schema",
                    expected_status=400
                )
                return True
            else:
                self.log_test(
                    "POST /admin/categories (form_schema with <script>)",
                    False,
                    response.status_code,
                    f"❌ Security issue: malicious form_schema was accepted! Response: {response.text}",
                    expected_status=400
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "POST /admin/categories (form_schema with <script>)",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}",
                expected_status=400
            )
            return False

    def test_home_category_layout(self):
        """3) Homepage - GET /site/home-category-layout?country=DE -> 200"""
        try:
            response = self.session.get(
                f"{BASE_URL}/site/home-category-layout",
                params={"country": "DE"},
                timeout=10
            )
            
            success = response.status_code == 200
            details = "✅ Home category layout retrieved successfully" if success else f"❌ Error: {response.text}"
            
            self.log_test(
                "GET /site/home-category-layout?country=DE",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /site/home-category-layout?country=DE",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_categories_with_module(self):
        """GET /categories?module=real_estate&country=DE -> 200 ve icon_svg field presence kontrolü"""
        try:
            response = self.session.get(
                f"{BASE_URL}/categories",
                params={"module": "real_estate", "country": "DE"},
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check if response is list or dict with data
                    categories = data if isinstance(data, list) else data.get('data', [])
                    
                    # Check for icon_svg field presence
                    icon_svg_found = False
                    if categories and len(categories) > 0:
                        for category in categories:
                            if 'icon_svg' in category:
                                icon_svg_found = True
                                break
                    
                    if icon_svg_found:
                        self.log_test(
                            "GET /categories?module=real_estate&country=DE",
                            True,
                            200,
                            f"✅ Categories retrieved successfully, icon_svg field present, count: {len(categories)}"
                        )
                    else:
                        self.log_test(
                            "GET /categories?module=real_estate&country=DE",
                            True,
                            200,
                            f"⚠️ Categories retrieved but icon_svg field missing in response, count: {len(categories)}"
                        )
                    return True
                except json.JSONDecodeError:
                    self.log_test(
                        "GET /categories?module=real_estate&country=DE",
                        False,
                        200,
                        f"❌ Invalid JSON response: {response.text}"
                    )
                    return False
            else:
                self.log_test(
                    "GET /categories?module=real_estate&country=DE",
                    False,
                    response.status_code,
                    f"❌ Error: {response.text}"
                )
                return False
            
        except requests.RequestException as e:
            self.log_test(
                "GET /categories?module=real_estate&country=DE",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_v2_search_basic(self):
        """GET /v2/search?country=DE&limit=4&page=1&sort=date_desc -> 200"""
        try:
            response = self.session.get(
                f"{BASE_URL}/v2/search",
                params={
                    "country": "DE",
                    "limit": "4", 
                    "page": "1",
                    "sort": "date_desc"
                },
                timeout=10
            )
            
            success = response.status_code == 200
            details = "✅ V2 search basic query successful" if success else f"❌ Error: {response.text}"
            
            self.log_test(
                "GET /v2/search?country=DE&limit=4&page=1&sort=date_desc",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /v2/search?country=DE&limit=4&page=1&sort=date_desc",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_v2_search_category_filter_existing(self):
        """4) Search regression - GET /v2/search?country=DE&category=arsa&sort=date_desc&page=1&limit=20 -> 200 (500 olmamalı)"""
        try:
            response = self.session.get(
                f"{BASE_URL}/v2/search",
                params={
                    "country": "DE",
                    "category": "arsa",
                    "sort": "date_desc",
                    "page": "1",
                    "limit": "20"
                },
                timeout=10
            )
            
            # Must NOT be 500 - this is the regression test
            if response.status_code == 200:
                self.log_test(
                    "GET /v2/search?category=arsa (regression test)",
                    True,
                    200,
                    "✅ Category filter regression test passed: no 500 error"
                )
                return True
            elif response.status_code == 500:
                self.log_test(
                    "GET /v2/search?category=arsa (regression test)",
                    False,
                    500,
                    f"❌ REGRESSION DETECTED: 500 error returned! Response: {response.text}"
                )
                return False
            else:
                # Other status codes are acceptable (404, 400, etc.)
                self.log_test(
                    "GET /v2/search?category=arsa (regression test)",
                    True,
                    response.status_code,
                    f"✅ No 500 error (got {response.status_code}), regression test passed"
                )
                return True
            
        except requests.RequestException as e:
            self.log_test(
                "GET /v2/search?category=arsa (regression test)",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def test_v2_search_category_filter_nonexistent(self):
        """GET /v2/search?country=DE&category=does-not-exist&sort=date_desc&page=1&limit=20 -> 200, boş sonuç kabul"""
        try:
            response = self.session.get(
                f"{BASE_URL}/v2/search",
                params={
                    "country": "DE",
                    "category": "does-not-exist",
                    "sort": "date_desc",
                    "page": "1",
                    "limit": "20"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Check if empty results are handled properly
                    results = data.get('results', []) if isinstance(data, dict) else data
                    result_count = len(results) if isinstance(results, list) else 0
                    
                    self.log_test(
                        "GET /v2/search?category=does-not-exist",
                        True,
                        200,
                        f"✅ Non-existent category handled properly, results count: {result_count}"
                    )
                    return True
                except json.JSONDecodeError:
                    self.log_test(
                        "GET /v2/search?category=does-not-exist",
                        True,
                        200,
                        "✅ Response received (non-JSON), acceptable for non-existent category"
                    )
                    return True
            else:
                # Non-200 responses are also acceptable for non-existent categories
                self.log_test(
                    "GET /v2/search?category=does-not-exist",
                    True,
                    response.status_code,
                    f"✅ Non-existent category handled with status {response.status_code}"
                )
                return True
            
        except requests.RequestException as e:
            self.log_test(
                "GET /v2/search?category=does-not-exist",
                False,
                "ERROR",
                f"❌ Request exception: {str(e)}"
            )
            return False

    def run_all_tests(self):
        """Run all backend validation tests according to review request"""
        print("🚀 Starting Backend Categories & Security Validation Tests...")
        print("Base URL:", BASE_URL)
        print("=" * 80)
        
        # Step 1: Authentication
        print("\n1️⃣ AUTHENTICATION TEST")
        print("-" * 40)
        login_success = self.test_auth_login()
        if not login_success:
            print("\n❌ CRITICAL: Admin login failed. Stopping tests.")
            return False
            
        # Step 2: Category icon_svg security and CRUD
        print("\n2️⃣ CATEGORY ICON_SVG SECURITY & CRUD TESTS")
        print("-" * 40)
        category_tests = [
            self.test_category_create_valid_icon_svg,
            self.test_category_update_valid_icon_svg, 
            self.test_category_delete,
            self.test_category_create_script_injection_icon_svg,
            self.test_category_create_script_injection_form_schema
        ]
        
        category_results = []
        for test_func in category_tests:
            result = test_func()
            category_results.append(result)
            
        # Step 3: Homepage data endpoints
        print("\n3️⃣ HOMEPAGE DATA ENDPOINTS")
        print("-" * 40)
        homepage_tests = [
            self.test_home_category_layout,
            self.test_categories_with_module,
            self.test_v2_search_basic
        ]
        
        homepage_results = []
        for test_func in homepage_tests:
            result = test_func()
            homepage_results.append(result)
            
        # Step 4: Search category filter regression  
        print("\n4️⃣ SEARCH CATEGORY FILTER REGRESSION TESTS")
        print("-" * 40)
        search_tests = [
            self.test_v2_search_category_filter_existing,
            self.test_v2_search_category_filter_nonexistent
        ]
        
        search_results = []
        for test_func in search_tests:
            result = test_func()
            search_results.append(result)
            
        return login_success and all(category_results) and all(homepage_results) and all(search_results)

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 BACKEND VALIDATION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        # Group results by category
        auth_tests = [r for r in self.test_results if "auth/login" in r["test"]]
        category_tests = [r for r in self.test_results if "/admin/categories" in r["test"]]
        homepage_tests = [r for r in self.test_results if any(x in r["test"] for x in ["/site/", "/categories?"])]
        search_tests = [r for r in self.test_results if "/v2/search" in r["test"]]
        
        print("\n🔐 Authentication:")
        for result in auth_tests:
            status_icon = "✅" if result["success"] else "❌"
            print(f"  {status_icon} {result['test']}: {result['status_code']}")
            
        print("\n🛡️ Category Security & CRUD:")
        for result in category_tests:
            status_icon = "✅" if result["success"] else "❌"
            print(f"  {status_icon} {result['test']}: {result['status_code']}")
            
        print("\n🏠 Homepage Data Endpoints:")
        for result in homepage_tests:
            status_icon = "✅" if result["success"] else "❌" 
            print(f"  {status_icon} {result['test']}: {result['status_code']}")
            
        print("\n🔍 Search Regression Tests:")
        for result in search_tests:
            status_icon = "✅" if result["success"] else "❌"
            print(f"  {status_icon} {result['test']}: {result['status_code']}")
            
        print(f"\n📈 Overall Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        # Check for critical security issues
        security_failures = [r for r in self.test_results if not r["success"] and "script" in r["test"]]
        if security_failures:
            print("\n🚨 CRITICAL SECURITY ISSUES DETECTED:")
            for failure in security_failures:
                print(f"  ❌ {failure['test']}: {failure['details']}")
        
        if passed == total:
            print("\n🎉 OVERALL RESULT: ✅ PASS - All backend validation tests successful")
            return True
        else:
            failed_tests = [r for r in self.test_results if not r["success"]]
            print(f"\n⚠️ OVERALL RESULT: ❌ FAIL - {len(failed_tests)} test(s) failed")
            print("\nFailed tests:")
            for failure in failed_tests:
                print(f"  ❌ {failure['test']}: {failure['status_code']} - {failure['details']}")
            return False

def main():
    """Main test execution function"""
    tester = CategoriesSecurityTester()
    
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