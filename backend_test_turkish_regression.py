#!/usr/bin/env python3

"""
Turkish Backend Regression Test

Base URL: https://page-builder-stable.preview.emergentagent.com
Users:
- Admin: admin@platform.com / Admin123!
- Dealer: dealer@platform.com / Dealer123!

Test kapsamı:
1) P0 regresyon:
   - POST /api/admin/categories (kategori create)
   - PATCH /api/admin/categories/{id} (kategori update)
   - DELETE /api/admin/categories/{id} (kategori delete)
   - PUT /api/admin/layouts/{revision_id}/publish ve scope conflict guard akışının bozulmaması
   - DELETE /api/admin/layouts/permanent (validation + active revision safety)
2) RBAC temel kontrol:
   - Dealer ile /api/admin/categories, /api/admin/layouts, /api/admin/revision-redirect-telemetry erişim 403 olmalı
3) Faz1 telemetry API:
   - GET /api/admin/revision-redirect-telemetry
   - summary alanlarında success_rate_pct, failure_rate_pct, daily_trend, slo var mı
   - trend_days parametresi (7/14/30) ile daily_trend uzunluğu eşleşiyor mu

Sonuçları PASS/FAIL ve endpoint bazlı kısa raporla dön.
"""

import requests
import json
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class TurkishRegressionTester:
    def __init__(self):
        self.base_url = "https://page-builder-stable.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Turkish-Regression-Tester/1.0'
        })
        self.results = []
        self.passed = 0
        self.failed = 0
        
        # Test credentials
        self.admin_credentials = {
            "email": "admin@platform.com", 
            "password": "Admin123!"
        }
        self.dealer_credentials = {
            "email": "dealer@platform.com",
            "password": "Dealer123!"
        }
        
        self.admin_token = None
        self.dealer_token = None
        
        # Test data storage
        self.created_category_id = None
        self.test_revision_id = None

    def authenticate_user(self, credentials: Dict[str, str], user_type: str = "admin") -> str:
        """Authenticate user and return access token"""
        print(f"\n🔐 Authenticating as {user_type}...")
        
        try:
            auth_url = f"{self.base_url}/auth/login"
            response = self.session.post(auth_url, json=credentials, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    token = data['access_token']
                    print(f"✅ {user_type.title()} authentication successful")
                    return token
                else:
                    print(f"❌ No access token in response: {data}")
                    return None
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None

    def setup_authentication(self) -> bool:
        """Setup authentication for both admin and dealer users"""
        self.admin_token = self.authenticate_user(self.admin_credentials, "admin")
        self.dealer_token = self.authenticate_user(self.dealer_credentials, "dealer")
        
        return self.admin_token is not None and self.dealer_token is not None

    def make_request(self, method: str, endpoint: str, token: str = None, data: dict = None, 
                    expected_status: int = 200) -> Tuple[int, dict]:
        """Make HTTP request with authentication"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_data = {}
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}
                
            return response.status_code, response_data
            
        except Exception as e:
            print(f"❌ Request error: {e}")
            return 0, {"error": str(e)}

    def log_test_result(self, test_name: str, endpoint: str, expected_status: int, 
                       actual_status: int, details: str = "", passed: bool = None):
        """Log test result"""
        if passed is None:
            passed = actual_status == expected_status
            
        result = {
            'test_name': test_name,
            'endpoint': endpoint,
            'expected_status': expected_status,
            'actual_status': actual_status,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results.append(result)
        
        if passed:
            self.passed += 1
            print(f"✅ PASS: {test_name}")
        else:
            self.failed += 1
            print(f"❌ FAIL: {test_name}")
            
        if details:
            print(f"   {details}")

    def test_p0_regression_category_crud(self):
        """Test P0 regression - Category CRUD operations"""
        print("\n" + "="*60)
        print("🔧 P0 REGRESSION: CATEGORY CRUD OPERATIONS")
        print("="*60)
        
        # 1. POST /api/admin/categories (kategori create)
        print("\n1️⃣ Testing Category Create...")
        
        # Use timestamp to ensure unique slug
        timestamp = str(int(datetime.now().timestamp()))
        
        category_data = {
            "name": f"Test Category Turkish Regression {timestamp}",
            "slug": f"test-category-turkish-regression-{timestamp}",
            "country_code": "TR",
            "module": "vehicle",
            "active_flag": True,
            "sort_order": 999,
            "parent_id": None
        }
        
        status, response = self.make_request('POST', '/admin/categories', self.admin_token, category_data)
        
        if status == 201 and 'category' in response and 'id' in response['category']:
            self.created_category_id = response['category']['id']
            self.log_test_result("Category Create", "POST /api/admin/categories", 201, status, 
                                f"Created category ID: {self.created_category_id}")
        else:
            self.log_test_result("Category Create", "POST /api/admin/categories", 201, status, 
                                f"Response: {response}")
        
        # 2. PATCH /api/admin/categories/{id} (kategori update)
        if self.created_category_id:
            print("\n2️⃣ Testing Category Update...")
            
            update_data = {
                "name": "Updated Test Category Turkish Regression"
            }
            
            status, response = self.make_request('PATCH', f'/admin/categories/{self.created_category_id}', 
                                                self.admin_token, update_data)
            
            self.log_test_result("Category Update", f"PATCH /api/admin/categories/{self.created_category_id}", 
                               200, status, f"Response: {response}")
        
        # 3. DELETE /api/admin/categories/{id} (kategori delete)
        if self.created_category_id:
            print("\n3️⃣ Testing Category Delete...")
            
            status, response = self.make_request('DELETE', f'/admin/categories/{self.created_category_id}', 
                                                self.admin_token)
            
            self.log_test_result("Category Delete", f"DELETE /api/admin/categories/{self.created_category_id}", 
                               200, status, f"Response: {response}")

    def test_p0_regression_layout_operations(self):
        """Test P0 regression - Layout operations"""
        print("\n" + "="*60)
        print("🎨 P0 REGRESSION: LAYOUT OPERATIONS")
        print("="*60)
        
        # First, let's get an existing revision to test with
        print("\n🔍 Finding existing layout revision to test...")
        
        status, response = self.make_request('GET', '/admin/layouts?limit=5', self.admin_token)
        
        if status == 200 and 'items' in response and response['items']:
            # Use first draft revision found
            for item in response['items']:
                if item.get('status') == 'draft' and item.get('is_active') == True:
                    self.test_revision_id = item['id']
                    print(f"   Found draft revision: {self.test_revision_id}")
                    break
            
            if not self.test_revision_id:
                # Use any revision if no draft found
                self.test_revision_id = response['items'][0]['id']
                print(f"   Using first available revision: {self.test_revision_id}")
        
        # 4. PUT /api/admin/layouts/{revision_id}/publish
        if self.test_revision_id:
            print("\n4️⃣ Testing Layout Publish...")
            
            status, response = self.make_request('PUT', f'/admin/layouts/{self.test_revision_id}/publish', 
                                                self.admin_token)
            
            # Accept both 200 (success) and 409 (conflict) as valid responses
            if status in [200, 409]:
                if status == 200:
                    conflict_info = response.get('conflict_resolution', {}) if isinstance(response, dict) else {}
                    conflict_count = conflict_info.get('conflict_count', 0)
                    details = f"Publish response: {conflict_count} conflicts handled"
                else:
                    detail_info = response.get('detail', {}) if isinstance(response, dict) else {}
                    if isinstance(detail_info, dict):
                        code = detail_info.get('code', 'unknown')
                    else:
                        code = str(detail_info)
                    details = f"Scope conflict detected (expected): {code}"
                    
                self.log_test_result("Layout Publish", f"PUT /api/admin/layouts/{self.test_revision_id}/publish", 
                                   status, status, details, passed=True)
            else:
                self.log_test_result("Layout Publish", f"PUT /api/admin/layouts/{self.test_revision_id}/publish", 
                                   200, status, f"Response: {response}")
        
        # 5. DELETE /api/admin/layouts/permanent
        print("\n5️⃣ Testing Layout Permanent Delete...")
        
        # Test with empty array first (should fail validation)
        delete_data = {"revision_ids": []}
        
        status, response = self.make_request('DELETE', '/admin/layouts/permanent', 
                                           self.admin_token, delete_data)
        
        if status == 422:  # Updated to expect 422 for validation errors
            self.log_test_result("Layout Permanent Delete - Validation", "DELETE /api/admin/layouts/permanent", 
                               422, status, "Validation correctly rejected empty revision_ids")
        else:
            self.log_test_result("Layout Permanent Delete - Validation", "DELETE /api/admin/layouts/permanent", 
                               422, status, f"Unexpected response: {response}")
        
        # Test with invalid UUID (should fail validation)
        delete_data = {"revision_ids": ["invalid-uuid"]}
        
        status, response = self.make_request('DELETE', '/admin/layouts/permanent', 
                                           self.admin_token, delete_data)
        
        if status in [400, 404]:
            self.log_test_result("Layout Permanent Delete - Invalid UUID", "DELETE /api/admin/layouts/permanent", 
                               status, status, "Correctly rejected invalid UUID", passed=True)
        else:
            self.log_test_result("Layout Permanent Delete - Invalid UUID", "DELETE /api/admin/layouts/permanent", 
                               400, status, f"Unexpected response: {response}")

    def test_rbac_controls(self):
        """Test RBAC controls - Dealer should get 403 on admin endpoints"""
        print("\n" + "="*60)
        print("🔒 RBAC CONTROLS: DEALER ACCESS RESTRICTIONS")
        print("="*60)
        
        # Test endpoints that dealer should NOT have access to
        restricted_endpoints = [
            ("GET", "/admin/categories", "Admin Categories List"),
            ("GET", "/admin/layouts", "Admin Layouts List"),  
            ("GET", "/admin/revision-redirect-telemetry", "Admin Telemetry"),
            ("POST", "/admin/categories", "Admin Category Create"),
        ]
        
        for method, endpoint, description in restricted_endpoints:
            print(f"\n🚫 Testing Dealer Access: {description}")
            
            test_data = None
            if method == 'POST' and 'categories' in endpoint:
                test_data = {"name": "Should Fail", "country_code": "TR", "module": "vehicle"}
            
            status, response = self.make_request(method, endpoint, self.dealer_token, test_data)
            
            if status == 403:
                self.log_test_result(f"RBAC - {description}", f"{method} {endpoint}", 
                                   403, status, "Correctly rejected dealer access")
            else:
                self.log_test_result(f"RBAC - {description}", f"{method} {endpoint}", 
                                   403, status, f"Unexpected status: {response}")

    def test_telemetry_api(self):
        """Test Faz1 telemetry API functionality"""
        print("\n" + "="*60)  
        print("📊 FAZ1 TELEMETRY API")
        print("="*60)
        
        # Test different trend_days parameters
        trend_days_tests = [7, 14, 30]
        
        for days in trend_days_tests:
            print(f"\n📈 Testing Telemetry with trend_days={days}...")
            
            status, response = self.make_request('GET', f'/admin/revision-redirect-telemetry?trend_days={days}', 
                                                self.admin_token)
            
            if status == 200:
                # Validate response structure - fields are under 'summary' key
                summary = response.get('summary', {})
                required_fields = ['success_rate_pct', 'failure_rate_pct', 'daily_trend', 'slo']
                missing_fields = []
                
                for field in required_fields:
                    if field not in summary:
                        missing_fields.append(field)
                
                # Check daily_trend length matches trend_days
                daily_trend = summary.get('daily_trend', [])
                trend_length_ok = len(daily_trend) == days
                
                if missing_fields:
                    self.log_test_result(f"Telemetry API - trend_days={days}", 
                                       f"GET /api/admin/revision-redirect-telemetry?trend_days={days}", 
                                       200, status, f"Missing fields in summary: {missing_fields}", passed=False)
                elif not trend_length_ok:
                    self.log_test_result(f"Telemetry API - trend_days={days}", 
                                       f"GET /api/admin/revision-redirect-telemetry?trend_days={days}", 
                                       200, status, f"daily_trend length {len(daily_trend)} != {days}", passed=False)
                else:
                    details = f"All required fields present in summary, daily_trend length: {len(daily_trend)} matches trend_days: {days}"
                    self.log_test_result(f"Telemetry API - trend_days={days}", 
                                       f"GET /api/admin/revision-redirect-telemetry?trend_days={days}", 
                                       200, status, details)
            else:
                self.log_test_result(f"Telemetry API - trend_days={days}", 
                                   f"GET /api/admin/revision-redirect-telemetry?trend_days={days}", 
                                   200, status, f"Response: {response}")

    def run_all_tests(self):
        """Run all Turkish regression tests"""
        print("🇹🇷 TURKISH BACKEND REGRESSION TEST")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Focus: P0 Regression + RBAC + Telemetry")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Setup authentication
        if not self.setup_authentication():
            print("❌ Failed to authenticate users. Aborting tests.")
            return False

        # Run test suites
        self.test_p0_regression_category_crud()
        self.test_p0_regression_layout_operations()
        self.test_rbac_controls()
        self.test_telemetry_api()
        
        # Cleanup any created test data
        self.cleanup_test_data()

        return True

    def cleanup_test_data(self):
        """Clean up any test data that was created"""
        if self.created_category_id:
            print(f"\n🧹 Cleaning up test category: {self.created_category_id}")
            try:
                status, response = self.make_request('DELETE', f'/admin/categories/{self.created_category_id}', 
                                                   self.admin_token)
                if status == 200:
                    print("✅ Test category cleaned up successfully")
                else:
                    print(f"⚠️ Failed to clean up test category: {response}")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")

    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.results)
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("🏁 TURKISH REGRESSION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Endpoint-based results
        print(f"\n📋 ENDPOINT-BASED RESULTS:")
        print("-" * 60)
        
        for result in self.results:
            status_icon = "✅" if result['passed'] else "❌"
            print(f"{status_icon} {result['test_name']} - {result['actual_status']}")
            if result['details']:
                print(f"    {result['details']}")
        
        # Final verdict
        print(f"\n🎯 KISA PASS/FAIL RAPORU:")
        if self.failed == 0:
            print(f"✅ PASS - All {self.passed} tests successful")
            print(f"🚀 P0 regression, RBAC controls, and telemetry API working correctly")
        else:
            print(f"❌ FAIL - {self.failed}/{total_tests} tests failed")
            print(f"⚠️ Issues found in backend regression testing")
        
        return self.failed == 0


def main():
    """Main execution function"""
    tester = TurkishRegressionTester()
    
    try:
        # Run all tests
        if not tester.run_all_tests():
            sys.exit(1)
        
        # Print summary
        success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()