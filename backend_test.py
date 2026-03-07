#!/usr/bin/env python3

"""
Final Backend Closure Check - Turkish Review Request
Testing specific API endpoints and page version validation.

Review Request: Final backend closure check
Base URL: https://layout-uniqueness.preview.emergentagent.com

A) Scope/page publish + version:
- TR/vehicle: home, urgent_listings, category_l0_l1, search_ln
- DE/global: home, urgent_listings, category_l0_l1, search_ln
- FR/global: home, urgent_listings, category_l0_l1, search_ln
- TR/global: home, urgent_listings, category_l0_l1, search_ln
Beklenen: page var + published revision var + payload_json.meta.template_version=finalized-p0-v1

B) Quick filter listings:
- /api/public/listings?country=TR&badge=urgent
- /api/public/listings?country=TR&badge=showcase
- /api/public/listings?country=TR&badge=campaign
Beklenen: 200 + query.badge doğru

C) Categories + ads + banners:
- /api/categories/tree?country=TR&depth=L1&module=vehicle
- /api/categories/children?country=TR&module=vehicle&depth=2
- /api/categories/listing-counts?country=TR&module=vehicle
- /api/ads/resolve?placement=home_top&country=TR
- /api/ads/resolve?placement=urgent_top&country=TR
- /api/banners?placement=category_top&country=TR
Beklenen: 200

Expected: Kısa PASS/FAIL raporu
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional


class FinalBackendClosureTester:
    def __init__(self):
        self.base_url = "https://layout-uniqueness.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Final-Backend-Closure-Tester/1.0'
        })
        self.results = []
        self.passed = 0
        self.failed = 0
        
        # Login credentials for admin authentication
        self.admin_credentials = {
            "email": "admin@platform.com",
            "password": "Admin123!"
        }
        self.auth_token = None

    def authenticate_admin(self) -> bool:
        """Authenticate as admin to access protected endpoints"""
        print("\n🔐 Authenticating as admin...")
        
        try:
            auth_url = f"{self.base_url}/auth/login"
            response = self.session.post(auth_url, json=self.admin_credentials, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'access_token' in data:
                    self.auth_token = data['access_token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.auth_token}'
                    })
                    print(f"✅ Admin authentication successful")
                    return True
                else:
                    print(f"❌ No access token in response: {data}")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def test_endpoint(self, endpoint: str, expected_status: int = 200, 
                     description: str = "", required_fields: List[str] = None,
                     check_badge: str = None, check_version: bool = False) -> Dict[str, Any]:
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
                            if self._check_nested_field(response_data, field):
                                validation_details.append(f"✅ Field '{field}' present")
                            else:
                                validation_details.append(f"❌ Field '{field}' missing")
                                content_pass = False
                    
                    # Badge validation for quick filter endpoints
                    if check_badge and 'query' in response_data:
                        if response_data.get('query', {}).get('badge') == check_badge:
                            validation_details.append(f"✅ Badge filter '{check_badge}' correct")
                        else:
                            validation_details.append(f"❌ Badge filter expected '{check_badge}', got '{response_data.get('query', {}).get('badge')}'")
                            content_pass = False
                    
                    # Version validation for page endpoints  
                    if check_version and 'revision' in response_data:
                        revision = response_data.get('revision', {})
                        payload = revision.get('payload_json', {}) if isinstance(revision, dict) else {}
                        meta = payload.get('meta', {}) if isinstance(payload, dict) else {}
                        template_version = meta.get('template_version')
                        
                        if template_version == 'finalized-p0-v1':
                            validation_details.append(f"✅ Template version '{template_version}' correct")
                        else:
                            validation_details.append(f"❌ Template version expected 'finalized-p0-v1', got '{template_version}'")
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
                        
                        # Page version details
                        if check_version:
                            revision = response_data.get('revision')
                            if revision and revision.get('status') == 'published':
                                validation_details.append(f"📄 Published revision: {revision.get('id')}")
                            else:
                                validation_details.append("❌ Published revision missing")
                                content_pass = False
                            
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

    def _check_nested_field(self, data: Dict, field_path: str) -> bool:
        """Check if a nested field exists in the response data"""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False
        return True

    def test_page_scope_and_version(self):
        """Test A) Scope/page publish + version validation"""
        print("\n" + "="*60)
        print("📄 SECTION A: PAGE SCOPE AND VERSION VALIDATION")
        print("="*60)
        
        # Page configurations to test
        page_configs = [
            # TR/vehicle pages
            ("TR", "vehicle", "home"),
            ("TR", "vehicle", "urgent_listings"), 
            ("TR", "vehicle", "category_l0_l1"),
            ("TR", "vehicle", "search_ln"),
            
            # DE/global pages
            ("DE", "global", "home"),
            ("DE", "global", "urgent_listings"),
            ("DE", "global", "category_l0_l1"), 
            ("DE", "global", "search_ln"),
            
            # FR/global pages
            ("FR", "global", "home"),
            ("FR", "global", "urgent_listings"),
            ("FR", "global", "category_l0_l1"),
            ("FR", "global", "search_ln"),
            
            # TR/global pages
            ("TR", "global", "home"),
            ("TR", "global", "urgent_listings"),
            ("TR", "global", "category_l0_l1"),
            ("TR", "global", "search_ln"),
        ]
        
        for country, module, page_type in page_configs:
            endpoint = f"/site/content-layout/resolve?page_type={page_type}&country={country}&module={module}"
            description = f"Page resolution for {country}/{module}/{page_type}"
            
            self.test_endpoint(
                endpoint,
                expected_status=200,
                description=description,
                required_fields=['revision.status', 'revision.payload_json.meta.template_version'],
                check_version=True
            )

    def test_quick_filter_listings(self):
        """Test B) Quick filter listings APIs"""
        print("\n" + "="*60)
        print("🚀 SECTION B: QUICK FILTER LISTINGS")
        print("="*60)
        
        # Quick filter badge tests
        quick_filters = [
            ("urgent", "Urgent listings with badge filter"),
            ("showcase", "Showcase listings with badge filter"), 
            ("campaign", "Campaign listings with badge filter")
        ]
        
        for badge, description in quick_filters:
            endpoint = f"/public/listings?country=TR&badge={badge}"
            
            self.test_endpoint(
                endpoint,
                expected_status=200,
                description=description,
                required_fields=['items', 'query'],
                check_badge=badge
            )

    def test_categories_ads_banners(self):
        """Test C) Categories + ads + banners APIs"""
        print("\n" + "="*60)
        print("🏗️ SECTION C: CATEGORIES, ADS AND BANNERS")
        print("="*60)
        
        # Categories APIs
        categories_tests = [
            ("/categories/tree?country=TR&depth=L1&module=vehicle", "Category tree for TR vehicle L1 depth"),
            ("/categories/children?country=TR&module=vehicle&depth=2", "Category children for TR vehicle depth 2"),
            ("/categories/listing-counts?country=TR&module=vehicle", "Listing counts for TR vehicle module")
        ]
        
        for endpoint, description in categories_tests:
            self.test_endpoint(endpoint, 200, description)
        
        # Ads APIs
        ads_tests = [
            ("/ads/resolve?placement=home_top&country=TR", "Ad resolution for home_top placement in TR"),
            ("/ads/resolve?placement=urgent_top&country=TR", "Ad resolution for urgent_top placement in TR")
        ]
        
        for endpoint, description in ads_tests:
            self.test_endpoint(endpoint, 200, description)
        
        # Banners API
        self.test_endpoint(
            "/banners?placement=category_top&country=TR",
            200,
            "Banners for category_top placement in TR"
        )

    def run_final_backend_closure_tests(self):
        """Run all final backend closure tests"""
        print("🏁 FINAL BACKEND CLOSURE CHECK")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Focus: Turkish Review Request - Final Backend Closure")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Authenticate admin (needed for some endpoints)
        if not self.authenticate_admin():
            print("⚠️ Admin authentication failed - continuing with public endpoints only")

        # Run test sections
        self.test_page_scope_and_version()
        self.test_quick_filter_listings()
        self.test_categories_ads_banners()

    def print_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.results)
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("🏁 FINAL BACKEND CLOSURE SUMMARY")
        print(f"{'='*60}")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS BY SECTION:")
        print("-" * 60)
        
        # Group results by section
        sections = {
            "A) PAGE SCOPE & VERSION": [],
            "B) QUICK FILTER LISTINGS": [],
            "C) CATEGORIES, ADS & BANNERS": []
        }
        
        for result in self.results:
            endpoint = result['endpoint']
            if '/site/content-layout/resolve' in endpoint:
                sections["A) PAGE SCOPE & VERSION"].append(result)
            elif '/public/listings' in endpoint and 'badge=' in endpoint:
                sections["B) QUICK FILTER LISTINGS"].append(result)
            else:
                sections["C) CATEGORIES, ADS & BANNERS"].append(result)
        
        for section_name, section_results in sections.items():
            if section_results:
                section_passed = sum(1 for r in section_results if r['overall_pass'])
                section_total = len(section_results)
                section_rate = (section_passed / section_total * 100) if section_total > 0 else 0
                
                print(f"\n{section_name}: {section_passed}/{section_total} ({section_rate:.0f}%)")
                
                for result in section_results:
                    status_icon = "✅" if result['overall_pass'] else "❌"
                    endpoint_short = result['endpoint'][:50] + "..." if len(result['endpoint']) > 50 else result['endpoint']
                    actual_status = result['actual_status']
                    
                    print(f"  {status_icon} {endpoint_short} ({actual_status})")
                    
                    # Show key validation details
                    if result['validation_details']:
                        for detail in result['validation_details'][:2]:  # Show first 2 details
                            print(f"      {detail}")
                    
                    if not result['overall_pass'] and 'error' in result:
                        print(f"      ⚠️ Error: {result['error']}")

        # Final verdict
        print(f"\n🎯 FINAL VERDICT:")
        if self.failed == 0:
            print(f"✅ ALL TESTS PASSED")
            print(f"🚀 All {self.passed} endpoints working correctly")
            print(f"🔥 Final backend closure: SUCCESSFUL")
        else:
            print(f"❌ {self.failed}/{total_tests} TESTS FAILED") 
            print(f"⚠️ Final backend closure: REQUIRES ATTENTION")
        
        # Kısa PASS/FAIL as requested
        verdict = "PASS" if self.failed == 0 else "FAIL"
        print(f"\n🏆 Kısa PASS/FAIL Raporu: {verdict}")
        
        if self.failed > 0:
            print(f"\n🔧 Failed Endpoints Summary:")
            for result in self.results:
                if not result['overall_pass']:
                    print(f"   ❌ {result['endpoint']} - {result['actual_status']}")
        
        return self.failed == 0


def main():
    """Main execution function"""
    tester = FinalBackendClosureTester()
    
    try:
        # Run the final backend closure tests
        tester.run_final_backend_closure_tests()
        
        # Print summary
        success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()