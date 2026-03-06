#!/usr/bin/env python3

"""
Backend Smoke Regression Test (Post Page-Composition Work)
Testing specific API endpoints as per review request.

Review Request: Backend smoke regression (post page-composition work)
Base URL: https://panel-manual-tr.preview.emergentagent.com

Test Endpoints:
1) GET /api/public/listings?country=TR&source=latest&limit=3&order=newest -> 200 + items/pagination
2) GET /api/categories/tree?country=TR&depth=L1&module=vehicle -> 200
3) GET /api/categories/listing-counts?country=TR&module=vehicle -> 200
4) GET /api/ads/resolve?placement=home_top&country=TR -> 200
5) GET /api/banners?placement=home_top&country=TR -> 200

Expected: Kısa PASS/FAIL result
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional


class SmokeRegressionTester:
    def __init__(self):
        self.base_url = "https://panel-manual-tr.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Smoke-Regression-Tester/1.0'
        })
        self.results = []
        self.passed = 0
        self.failed = 0

    def test_endpoint(self, endpoint: str, expected_status: int = 200, 
                     description: str = "", required_fields: List[str] = None) -> Dict[str, Any]:
        """Test a single API endpoint with validation"""
        url = f"{self.base_url}{endpoint}"
        
        print(f"\n🔍 Testing: {endpoint}")
        print(f"📝 {description}")
        print(f"🌐 URL: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            status_code = response.status_code
            
            print(f"📊 Response Status: {status_code} (expected: {expected_status})")
            
            # Status code check
            status_pass = status_code == expected_status
            
            # Content validation
            content_pass = True
            response_data = None
            validation_details = []
            
            if status_code == 200:
                try:
                    response_data = response.json()
                    validation_details.append("✅ Valid JSON response")
                    
                    # Check required fields
                    if required_fields:
                        for field in required_fields:
                            if field in response_data:
                                validation_details.append(f"✅ Field '{field}' present")
                            else:
                                validation_details.append(f"❌ Field '{field}' missing")
                                content_pass = False
                    
                    # Print response structure info
                    if isinstance(response_data, dict):
                        keys = list(response_data.keys())
                        print(f"🔑 Response Keys: {keys}")
                        
                        # Special validations for specific endpoints
                        if 'items' in response_data:
                            items_count = len(response_data['items']) if isinstance(response_data['items'], list) else 0
                            print(f"📦 Items Count: {items_count}")
                            validation_details.append(f"📦 Items: {items_count} found")
                        
                        if 'pagination' in response_data:
                            print(f"📄 Pagination: {response_data['pagination']}")
                            validation_details.append("📄 Pagination data present")
                        
                        if 'data' in response_data and isinstance(response_data['data'], list):
                            data_count = len(response_data['data'])
                            print(f"📊 Data Count: {data_count}")
                            validation_details.append(f"📊 Data: {data_count} items")
                            
                except json.JSONDecodeError as e:
                    validation_details.append(f"❌ Invalid JSON: {e}")
                    content_pass = False
                    
            elif status_code in [400, 401, 403, 404, 500]:
                # For error responses, try to parse error message
                try:
                    error_data = response.json()
                    print(f"❗ Error Response: {error_data}")
                except:
                    print(f"❗ Raw Error: {response.text[:200]}")
            
            # Overall test result
            overall_pass = status_pass and content_pass
            
            result = {
                'endpoint': endpoint,
                'description': description,
                'url': url,
                'expected_status': expected_status,
                'actual_status': status_code,
                'status_pass': status_pass,
                'content_pass': content_pass,
                'overall_pass': overall_pass,
                'validation_details': validation_details,
                'response_data': response_data,
                'timestamp': datetime.now().isoformat()
            }
            
            if overall_pass:
                print("✅ PASS")
                self.passed += 1
            else:
                print("❌ FAIL")
                self.failed += 1
                
            self.results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"💥 Network Error: {e}")
            result = {
                'endpoint': endpoint,
                'description': description,
                'url': url,
                'expected_status': expected_status,
                'actual_status': 'ERROR',
                'status_pass': False,
                'content_pass': False,
                'overall_pass': False,
                'validation_details': [f"❌ Network Error: {e}"],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            self.failed += 1
            print("❌ FAIL")
            return result

    def run_smoke_tests(self):
        """Run all backend smoke regression tests"""
        print("🚀 BACKEND SMOKE REGRESSION TEST")
        print("="*50)
        print(f"Base URL: {self.base_url}")
        print(f"Test Focus: Post Page-Composition Work")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)

        # Test 1: Public Listings API
        self.test_endpoint(
            "/public/listings?country=TR&source=latest&limit=3&order=newest",
            expected_status=200,
            description="Public listings with Turkish locale, latest source, limit 3, newest order",
            required_fields=['items', 'pagination']
        )

        # Test 2: Categories Tree API  
        self.test_endpoint(
            "/categories/tree?country=TR&depth=L1&module=vehicle",
            expected_status=200,
            description="Category tree for Turkey, L1 depth, vehicle module"
        )

        # Test 3: Category Listing Counts API
        self.test_endpoint(
            "/categories/listing-counts?country=TR&module=vehicle", 
            expected_status=200,
            description="Listing counts per category for Turkey vehicle module"
        )

        # Test 4: Ads Resolution API
        self.test_endpoint(
            "/ads/resolve?placement=home_top&country=TR",
            expected_status=200,
            description="Ad resolution for home_top placement in Turkey"
        )

        # Test 5: Banners API
        self.test_endpoint(
            "/banners?placement=home_top&country=TR",
            expected_status=200,
            description="Banners for home_top placement in Turkey"
        )

    def print_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.results)
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("🏁 SMOKE REGRESSION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        print("-" * 40)
        
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result['overall_pass'] else "❌"
            endpoint = result['endpoint']
            actual_status = result['actual_status']
            expected_status = result['expected_status']
            
            print(f"{i}. {status_icon} {endpoint}")
            print(f"   Status: {actual_status} (expected: {expected_status})")
            
            if result['validation_details']:
                for detail in result['validation_details']:
                    print(f"   {detail}")
            
            if not result['overall_pass']:
                if 'error' in result:
                    print(f"   ⚠️  Error: {result['error']}")
            print()

        # Final verdict
        print(f"🎯 FINAL VERDICT:")
        if self.failed == 0:
            print(f"✅ ALL TESTS PASSED")
            print(f"🚀 All {self.passed} endpoints working correctly")
            print(f"🔥 Backend smoke regression: SUCCESSFUL")
        else:
            print(f"❌ {self.failed}/{total_tests} TESTS FAILED")
            print(f"⚠️  Backend smoke regression: REQUIRES ATTENTION")
        
        # Kısa PASS/FAIL as requested
        verdict = "PASS" if self.failed == 0 else "FAIL"
        print(f"\n🏆 Kısa PASS/FAIL: {verdict}")
        
        return self.failed == 0


def main():
    """Main execution function"""
    tester = SmokeRegressionTester()
    
    try:
        # Run the smoke tests
        tester.run_smoke_tests()
        
        # Print summary
        success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()