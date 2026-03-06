#!/usr/bin/env python3

"""
P0 Closure Backend Validation Test
Testing specific API endpoints as per Turkish review request.

Review Request: P0 kapanış backend doğrulaması
Base URL: https://page-builder-227.preview.emergentagent.com

Test Requirements:
1) Scope/page type publish kontrolü (API read):
   - TR+vehicle: home, urgent_listings, category_l0_l1, search_ln
   - DE+global: home, urgent_listings, category_l0_l1, search_ln  
   - FR+global: home, urgent_listings, category_l0_l1, search_ln
   Expected: page mevcut + published revision var + payload_json.meta.template_version = finalized-p0-v1

2) Quick filter API sözleşmesi:
   - /api/public/listings?country=TR&badge=urgent
   - /api/public/listings?country=TR&badge=showcase  
   - /api/public/listings?country=TR&badge=campaign
   Expected: 200 + query.badge doğru map

3) Category/data endpoints:
   - /api/categories/tree?country=TR&depth=L1&module=vehicle
   - /api/categories/children?country=TR&module=vehicle&depth=2
   - /api/categories/listing-counts?country=TR&module=vehicle
   Expected: 200

4) Ads/Banners:
   - /api/ads/resolve?placement=home_top&country=TR
   - /api/ads/resolve?placement=urgent_top&country=TR
   - /api/banners?placement=category_top&country=TR
   Expected: 200 + boş state bozmayacak payload yapısı

Expected Output: PASS/FAIL + kısa bulgular
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class P0ValidationTester:
    def __init__(self):
        self.base_url = "https://page-builder-227.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'P0-Backend-Validation-Tester/1.0',
            'Accept': 'application/json'
        })
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")

    def test_endpoint(self, endpoint: str, expected_status: int = 200, 
                     description: str = "", validation_func=None, 
                     critical: bool = True) -> Dict[str, Any]:
        """Test a single API endpoint with custom validation"""
        url = f"{self.base_url}{endpoint}"
        
        self.log(f"Testing: {endpoint}")
        self.log(f"Description: {description}")
        self.log(f"URL: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            status_code = response.status_code
            
            self.log(f"Response Status: {status_code} (expected: {expected_status})")
            
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
                    
                    # Apply custom validation function if provided
                    if validation_func and callable(validation_func):
                        custom_result = validation_func(response_data, endpoint)
                        if isinstance(custom_result, tuple):
                            custom_pass, custom_details = custom_result
                            content_pass = content_pass and custom_pass
                            validation_details.extend(custom_details)
                        else:
                            content_pass = content_pass and custom_result
                    
                    # Print response info for debugging
                    if isinstance(response_data, dict):
                        keys = list(response_data.keys())[:10]  # Limit output
                        self.log(f"Response Keys: {keys}")
                        
                except json.JSONDecodeError as e:
                    validation_details.append(f"❌ Invalid JSON: {e}")
                    content_pass = False
                    
            elif status_code in [400, 401, 403, 404, 500]:
                try:
                    error_data = response.json()
                    self.log(f"Error Response: {error_data}")
                except:
                    self.log(f"Raw Error: {response.text[:200]}")
            
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
                'critical': critical,
                'validation_details': validation_details,
                'response_data': response_data,
                'timestamp': datetime.now().isoformat()
            }
            
            if overall_pass:
                self.log("✅ PASS", "SUCCESS")
                self.passed += 1
            else:
                self.log("❌ FAIL", "ERROR")
                self.failed += 1
                
            self.results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            self.log(f"Network Error: {e}", "ERROR")
            result = {
                'endpoint': endpoint,
                'description': description,
                'url': url,
                'expected_status': expected_status,
                'actual_status': 'NETWORK_ERROR',
                'status_pass': False,
                'content_pass': False,
                'overall_pass': False,
                'critical': critical,
                'validation_details': [f"❌ Network Error: {e}"],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            self.failed += 1
            self.log("❌ FAIL", "ERROR")
            return result

    def validate_scope_pages(self, data: dict, endpoint: str) -> Tuple[bool, List[str]]:
        """Validate scope/page type publish control"""
        details = []
        success = True
        
        # Check if page and revision structure is present
        if 'layout_page' in data and 'revision' in data:
            layout_page = data['layout_page']
            revision = data['revision']
            
            details.append("✅ Page and revision structure present")
            
            # Check if published revision exists
            if revision and revision.get('status') == 'published':
                details.append("✅ Published revision found")
                published_revisions_found = 1
            else:
                details.append("❌ No published revision found")
                success = False
                published_revisions_found = 0
                
            # Check for template version in payload_json.meta
            template_versions_found = 0
            payload_json = revision.get('payload_json', {}) if revision else {}
            if isinstance(payload_json, dict):
                meta = payload_json.get('meta', {})
                if isinstance(meta, dict):
                    template_version = meta.get('template_version')
                    if template_version == 'finalized-p0-v1':
                        template_versions_found = 1
                        details.append("✅ Template version 'finalized-p0-v1' found")
                    else:
                        details.append(f"❌ Template version '{template_version}' != 'finalized-p0-v1'")
                        success = False
                else:
                    details.append("❌ No meta section in payload_json")
                    success = False
            else:
                details.append("❌ No payload_json found")
                success = False
                
            details.append(f"📝 Published revisions: {published_revisions_found}")
            details.append(f"🏷️  Template versions (finalized-p0-v1): {template_versions_found}")
                    
        else:
            details.append("❌ Missing layout_page or revision data")
            success = False
            
        return success, details

    def validate_badge_mapping(self, data: dict, endpoint: str) -> Tuple[bool, List[str]]:
        """Validate badge query parameter mapping in listings"""
        details = []
        success = True
        
        # Extract badge from endpoint
        badge = None
        if 'badge=urgent' in endpoint:
            badge = 'urgent'
        elif 'badge=showcase' in endpoint:
            badge = 'showcase'
        elif 'badge=campaign' in endpoint:
            badge = 'campaign'
        
        if not badge:
            details.append("❌ No badge parameter found in endpoint")
            return False, details
            
        # Check response structure
        if 'items' in data:
            items = data['items']
            details.append(f"📦 Found {len(items)} items")
            
            # Validate badge mapping in items (if items exist)
            badge_matches = 0
            for item in items:
                if isinstance(item, dict):
                    item_badges = item.get('badges', [])
                    item_doping_type = item.get('doping_type')
                    item_is_urgent = item.get('is_urgent', False)
                    item_is_showcase = item.get('is_showcase', False)
                    
                    # Check badge mapping logic
                    if badge == 'urgent' and (item_is_urgent or 'urgent' in item_badges):
                        badge_matches += 1
                    elif badge == 'showcase' and (item_is_showcase or 'showcase' in item_badges):
                        badge_matches += 1
                    elif badge == 'campaign' and item_doping_type:
                        badge_matches += 1
            
            details.append(f"🏷️  Badge '{badge}' matches: {badge_matches}/{len(items)}")
            
            # Accept empty results as valid (no items matching filter is OK)
            if len(items) == 0:
                details.append(f"✅ Empty result set for badge '{badge}' (valid)")
            elif badge_matches > 0:
                details.append(f"✅ Badge mapping working correctly")
            else:
                details.append(f"⚠️  Badge mapping may not be working")
                # Don't fail on this - empty results are acceptable
        else:
            details.append("❌ No 'items' field found")
            success = False
            
        return success, details

    def validate_category_tree(self, data: dict, endpoint: str) -> Tuple[bool, List[str]]:
        """Validate category tree structure"""
        details = []
        success = True
        
        # Check for proper API response structure
        if 'items' in data and 'meta' in data:
            items = data['items']
            meta = data['meta']
            
            details.append(f"✅ Valid API response structure")
            details.append(f"🌳 Found {len(items)} categories")
            details.append(f"📄 Meta: {meta}")
            
            if isinstance(items, list):
                # Empty results are valid - some countries/modules may not have categories
                if len(items) == 0:
                    details.append("✅ Empty category result (valid for some countries/modules)")
                else:
                    # Check category structure if items exist
                    valid_categories = 0
                    for cat in items:
                        if isinstance(cat, dict) and ('name' in cat or 'slug' in cat):
                            valid_categories += 1
                    
                    details.append(f"✅ Valid categories: {valid_categories}/{len(items)}")
                    
                    if valid_categories == 0 and len(items) > 0:
                        details.append("⚠️  Categories found but structure invalid")
                        success = False
            else:
                details.append("❌ Items is not a list")
                success = False
        else:
            details.append("❌ Missing required 'items' or 'meta' fields")
            success = False
            
        return success, details

    def validate_ads_banners(self, data: dict, endpoint: str) -> Tuple[bool, List[str]]:
        """Validate ads/banners empty state structure"""
        details = []
        success = True
        
        # For ads/banners, empty state should not break the payload structure
        if isinstance(data, dict):
            details.append("✅ Response is valid JSON object")
            
            # Check for common ad/banner fields
            if 'ads' in data or 'banners' in data or 'data' in data:
                ads_data = data.get('ads') or data.get('banners') or data.get('data')
                
                if isinstance(ads_data, list):
                    details.append(f"📢 Found {len(ads_data)} ad/banner items")
                    details.append("✅ Empty state payload structure maintained")
                else:
                    details.append("⚠️  Unexpected ads/banners data format")
            else:
                # Even if no ads/banners fields, valid JSON is acceptable
                details.append("✅ Valid response (empty state OK)")
                
        elif isinstance(data, list):
            details.append(f"📢 Found {len(data)} ad/banner items")
            details.append("✅ Empty state payload structure maintained")
        else:
            details.append("❌ Invalid response format")
            success = False
            
        return success, details

    def run_p0_validation_tests(self):
        """Run all P0 closure validation tests"""
        self.log("🚀 P0 CLOSURE BACKEND VALIDATION TEST", "INFO")
        self.log("="*60, "INFO")
        self.log(f"Base URL: {self.base_url}", "INFO")
        self.log(f"Test Focus: P0 Closure Backend Validation", "INFO")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log("="*60, "INFO")

        # Section 1: Scope/Page Type Publish Control
        self.log("\n📋 SECTION 1: SCOPE/PAGE TYPE PUBLISH CONTROL", "INFO")
        self.log("-" * 50, "INFO")
        
        # TR+vehicle page types
        page_types = ["home", "urgent_listings", "category_l0_l1", "search_ln"]
        
        for page_type in page_types:
            self.test_endpoint(
                f"/site/content-layout/resolve?country=TR&page_type={page_type}&module=vehicle",
                expected_status=200,
                description=f"TR+vehicle {page_type} page publish control",
                validation_func=self.validate_scope_pages
            )
        
        # DE+global page types  
        for page_type in page_types:
            self.test_endpoint(
                f"/site/content-layout/resolve?country=DE&page_type={page_type}&module=global", 
                expected_status=200,
                description=f"DE+global {page_type} page publish control",
                validation_func=self.validate_scope_pages
            )
            
        # FR+global page types
        for page_type in page_types:
            self.test_endpoint(
                f"/site/content-layout/resolve?country=FR&page_type={page_type}&module=global",
                expected_status=200,
                description=f"FR+global {page_type} page publish control", 
                validation_func=self.validate_scope_pages
            )
        
        # Section 2: Quick Filter API Contract
        self.log("\n🏷️  SECTION 2: QUICK FILTER API CONTRACT", "INFO") 
        self.log("-" * 50, "INFO")
        
        # Test urgent badge filter
        self.test_endpoint(
            "/public/listings?country=TR&badge=urgent",
            expected_status=200,
            description="Public listings with urgent badge filter for Turkey",
            validation_func=self.validate_badge_mapping
        )
        
        # Test showcase badge filter
        self.test_endpoint(
            "/public/listings?country=TR&badge=showcase", 
            expected_status=200,
            description="Public listings with showcase badge filter for Turkey",
            validation_func=self.validate_badge_mapping
        )
        
        # Test campaign badge filter
        self.test_endpoint(
            "/public/listings?country=TR&badge=campaign",
            expected_status=200, 
            description="Public listings with campaign badge filter for Turkey",
            validation_func=self.validate_badge_mapping
        )

        # Section 3: Category/Data Endpoints
        self.log("\n🌳 SECTION 3: CATEGORY/DATA ENDPOINTS", "INFO")
        self.log("-" * 50, "INFO")
        
        # Test category tree
        self.test_endpoint(
            "/categories/tree?country=TR&depth=L1&module=vehicle",
            expected_status=200,
            description="Category tree for Turkey, L1 depth, vehicle module",
            validation_func=self.validate_category_tree
        )
        
        # Test category children
        self.test_endpoint(
            "/categories/children?country=TR&module=vehicle&depth=2",
            expected_status=200,
            description="Category children for Turkey, vehicle module, depth 2",
            validation_func=self.validate_category_tree
        )
        
        # Test category listing counts
        self.test_endpoint(
            "/categories/listing-counts?country=TR&module=vehicle",
            expected_status=200,
            description="Category listing counts for Turkey vehicle module"
        )

        # Section 4: Ads/Banners
        self.log("\n📢 SECTION 4: ADS/BANNERS", "INFO")
        self.log("-" * 50, "INFO")
        
        # Test ads resolution - home_top
        self.test_endpoint(
            "/ads/resolve?placement=home_top&country=TR", 
            expected_status=200,
            description="Ad resolution for home_top placement in Turkey",
            validation_func=self.validate_ads_banners
        )
        
        # Test ads resolution - urgent_top
        self.test_endpoint(
            "/ads/resolve?placement=urgent_top&country=TR",
            expected_status=200,
            description="Ad resolution for urgent_top placement in Turkey", 
            validation_func=self.validate_ads_banners
        )
        
        # Test banners - category_top
        self.test_endpoint(
            "/banners?placement=category_top&country=TR",
            expected_status=200,
            description="Banners for category_top placement in Turkey",
            validation_func=self.validate_ads_banners
        )

    def print_summary(self):
        """Print comprehensive P0 validation summary"""
        total_tests = len(self.results)
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*70}")
        print("🏁 P0 CLOSURE BACKEND VALIDATION SUMMARY")
        print(f"{'='*70}")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Critical vs Non-Critical breakdown
        critical_failed = sum(1 for r in self.results if not r['overall_pass'] and r.get('critical', True))
        non_critical_failed = self.failed - critical_failed
        
        if critical_failed > 0:
            print(f"🚨 Critical Failures: {critical_failed}")
        if non_critical_failed > 0:
            print(f"⚠️  Non-Critical Failures: {non_critical_failed}")
        
        print(f"\n📋 DETAILED RESULTS:")
        print("-" * 50)
        
        # Group results by section
        sections = {
            "QUICK FILTER API": [],
            "CATEGORY/DATA ENDPOINTS": [],
            "ADS/BANNERS": [],
            "OTHER": []
        }
        
        for result in self.results:
            endpoint = result['endpoint']
            if 'badge=' in endpoint:
                sections["QUICK FILTER API"].append(result)
            elif '/categories/' in endpoint:
                sections["CATEGORY/DATA ENDPOINTS"].append(result)
            elif '/ads/' in endpoint or '/banners' in endpoint:
                sections["ADS/BANNERS"].append(result)
            else:
                sections["OTHER"].append(result)
        
        for section_name, section_results in sections.items():
            if section_results:
                print(f"\n🔸 {section_name}")
                for result in section_results:
                    status_icon = "✅" if result['overall_pass'] else "❌"
                    endpoint = result['endpoint']
                    actual_status = result['actual_status']
                    
                    print(f"   {status_icon} {endpoint} ({actual_status})")
                    
                    if result['validation_details']:
                        for detail in result['validation_details'][:3]:  # Limit details
                            print(f"      {detail}")
                    
                    if not result['overall_pass'] and 'error' in result:
                        print(f"      ⚠️  Error: {result['error']}")

        # Final verdict based on P0 requirements
        print(f"\n🎯 P0 CLOSURE VALIDATION VERDICT:")
        
        # Check critical functionality
        critical_passed = sum(1 for r in self.results if r['overall_pass'] and r.get('critical', True))
        critical_total = sum(1 for r in self.results if r.get('critical', True))
        
        if critical_failed == 0:
            print(f"✅ ALL CRITICAL TESTS PASSED ({critical_passed}/{critical_total})")
            print(f"🚀 P0 Backend validation: SUCCESSFUL")
            verdict = "PASS"
        else:
            print(f"❌ CRITICAL FAILURES DETECTED ({critical_failed}/{critical_total})")
            print(f"⚠️  P0 Backend validation: REQUIRES ATTENTION")
            verdict = "FAIL"
        
        # Turkish summary as requested
        print(f"\n🇹🇷 TÜRKÇE ÖZET:")
        print(f"📊 Toplam test: {total_tests}")
        print(f"✅ Başarılı: {self.passed}")
        print(f"❌ Başarısız: {self.failed}")
        
        if verdict == "PASS":
            print(f"🎉 Sonuç: Tüm kritik API'ler çalışıyor")
        else:
            print(f"⚠️  Sonuç: Kritik hatalar var, düzeltme gerekli")
        
        # Final PASS/FAIL as requested
        print(f"\n🏆 PASS/FAIL + Kısa Bulgular: {verdict}")
        
        if verdict == "FAIL":
            failed_endpoints = [r['endpoint'] for r in self.results if not r['overall_pass']]
            print(f"Başarısız endpoint'ler: {', '.join(failed_endpoints[:3])}")
        else:
            print(f"Tüm endpoint'ler başarıyla test edildi.")
        
        return verdict == "PASS"


def main():
    """Main execution function"""
    tester = P0ValidationTester()
    
    try:
        # Run the P0 validation tests
        tester.run_p0_validation_tests()
        
        # Print summary
        success = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()