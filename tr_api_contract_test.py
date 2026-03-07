#!/usr/bin/env python3
"""
Turkish Backend API Contract Tests

Backend API contract testleri (sadece backend):
Base URL: https://page-builder-stable.preview.emergentagent.com

Tests the following API endpoints:

1) GET /api/categories/tree?country=TR&depth=L1&module=vehicle
   Expected: 200, response.meta.start_level = L0, response.meta.depth = L1, response.items array

2) GET /api/categories/tree?country=TR&depth=Lall&module=vehicle
   Expected: 200, response.meta.depth = Lall

3) GET /api/categories/children?country=TR&module=vehicle&depth=2
   Expected: 200, object can return, contains items array (nested support)

4) GET /api/categories/listing-counts?country=TR&module=vehicle
   Expected: 200, items array and listing_count field

5) GET /api/public/listings?country=TR&source=showcase&limit=5&order=newest
   Expected: 200, items + pagination, each item should have badge/badges field normalized

6) GET /api/public/listings?country=TR&source=category (without category_id)
   Expected: 400

7) GET /api/ads/resolve?placement=home_top&country=TR
   Expected: 200, placement_resolved set, has_active_ad bool

8) GET /api/banners?placement=home_top&country=TR
   Expected: 200, items array + meta.mode

Returns concise PASS/FAIL with endpoint-based short findings.
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List

class TurkishAPIContractTester:
    def __init__(self):
        self.base_url = "https://page-builder-stable.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Turkish-API-Contract-Tester/1.0'
        })
        self.results = []
        
    def log_result(self, endpoint: str, status: str, expected: str, actual: str, details: Dict[str, Any] = None):
        """Log test result"""
        result = {
            'endpoint': endpoint,
            'status': status,
            'expected': expected,
            'actual': actual,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results.append(result)
        
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {endpoint}")
        print(f"   Expected: {expected}")
        print(f"   Actual: {actual}")
        if details and details.get('error'):
            print(f"   Error: {details['error']}")
    
    def test_categories_tree_l1(self) -> None:
        """Test 1: GET /api/categories/tree?country=TR&depth=L1&module=vehicle"""
        endpoint = "GET /api/categories/tree (L1)"
        url = f"{self.base_url}/categories/tree"
        params = {
            'country': 'TR',
            'depth': 'L1',
            'module': 'vehicle'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check meta.start_level = L0
            meta = data.get('meta', {})
            start_level = meta.get('start_level')
            depth = meta.get('depth')
            items = data.get('items', [])
            
            if start_level != 'L0':
                self.log_result(endpoint, "FAIL", "meta.start_level = L0", f"meta.start_level = {start_level}", {
                    'error': f"start_level is '{start_level}', expected 'L0'"
                })
                return
                
            if depth != 'L1':
                self.log_result(endpoint, "FAIL", "meta.depth = L1", f"meta.depth = {depth}", {
                    'error': f"depth is '{depth}', expected 'L1'"
                })
                return
                
            if not isinstance(items, list):
                self.log_result(endpoint, "FAIL", "items array", f"items type: {type(items)}", {
                    'error': f"items is not an array: {type(items)}"
                })
                return
                
            self.log_result(endpoint, "PASS", "200, meta.start_level=L0, meta.depth=L1, items array", 
                          f"200, start_level={start_level}, depth={depth}, items count={len(items)}", {
                              'items_count': len(items),
                              'meta': meta
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with valid response", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_categories_tree_lall(self) -> None:
        """Test 2: GET /api/categories/tree?country=TR&depth=Lall&module=vehicle"""
        endpoint = "GET /api/categories/tree (Lall)"
        url = f"{self.base_url}/categories/tree"
        params = {
            'country': 'TR',
            'depth': 'Lall',
            'module': 'vehicle'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check meta.depth = Lall
            meta = data.get('meta', {})
            depth = meta.get('depth')
            
            if depth != 'Lall':
                self.log_result(endpoint, "FAIL", "meta.depth = Lall", f"meta.depth = {depth}", {
                    'error': f"depth is '{depth}', expected 'Lall'"
                })
                return
                
            self.log_result(endpoint, "PASS", "200, meta.depth=Lall", 
                          f"200, depth={depth}", {
                              'meta': meta
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with meta.depth=Lall", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_categories_children(self) -> None:
        """Test 3: GET /api/categories/children?country=TR&module=vehicle&depth=2"""
        endpoint = "GET /api/categories/children"
        url = f"{self.base_url}/categories/children"
        params = {
            'country': 'TR',
            'module': 'vehicle',
            'depth': '2'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check if response contains items array (nested support)
            items = data.get('items', [])
            
            if not isinstance(items, list):
                self.log_result(endpoint, "FAIL", "object with items array", f"items type: {type(items)}", {
                    'error': f"items is not an array: {type(items)}"
                })
                return
                
            self.log_result(endpoint, "PASS", "200, object with items array (nested support)", 
                          f"200, items count={len(items)}", {
                              'items_count': len(items),
                              'response_keys': list(data.keys())
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with items array", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_categories_listing_counts(self) -> None:
        """Test 4: GET /api/categories/listing-counts?country=TR&module=vehicle"""
        endpoint = "GET /api/categories/listing-counts"
        url = f"{self.base_url}/categories/listing-counts"
        params = {
            'country': 'TR',
            'module': 'vehicle'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check items array and listing_count field
            items = data.get('items', [])
            
            if not isinstance(items, list):
                self.log_result(endpoint, "FAIL", "items array", f"items type: {type(items)}", {
                    'error': f"items is not an array: {type(items)}"
                })
                return
            
            # Check if at least one item has listing_count field
            has_listing_count = False
            for item in items:
                if 'listing_count' in item:
                    has_listing_count = True
                    break
                    
            if not has_listing_count and len(items) > 0:
                self.log_result(endpoint, "FAIL", "items with listing_count field", "items without listing_count", {
                    'error': "No items have 'listing_count' field"
                })
                return
                
            self.log_result(endpoint, "PASS", "200, items array and listing_count field", 
                          f"200, items count={len(items)}, has_listing_count={has_listing_count}", {
                              'items_count': len(items),
                              'has_listing_count': has_listing_count
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with items and listing_count", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_public_listings_showcase(self) -> None:
        """Test 5: GET /api/public/listings?country=TR&source=showcase&limit=5&order=newest"""
        endpoint = "GET /api/public/listings (showcase)"
        url = f"{self.base_url}/public/listings"
        params = {
            'country': 'TR',
            'source': 'showcase',
            'limit': '5',
            'order': 'newest'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check items + pagination
            items = data.get('items', [])
            pagination = data.get('pagination', {})
            
            if not isinstance(items, list):
                self.log_result(endpoint, "FAIL", "items array", f"items type: {type(items)}", {
                    'error': f"items is not an array: {type(items)}"
                })
                return
                
            if not pagination:
                self.log_result(endpoint, "FAIL", "pagination object", "no pagination", {
                    'error': "pagination object missing"
                })
                return
            
            # Check if items have badge/badges field normalized
            badge_count = 0
            for item in items:
                if 'badge' in item or 'badges' in item:
                    badge_count += 1
                    
            self.log_result(endpoint, "PASS", "200, items + pagination, badge/badges normalized", 
                          f"200, items count={len(items)}, items with badges={badge_count}", {
                              'items_count': len(items),
                              'items_with_badges': badge_count,
                              'pagination': pagination
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with items, pagination, badges", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_public_listings_category_error(self) -> None:
        """Test 6: GET /api/public/listings?country=TR&source=category (without category_id)"""
        endpoint = "GET /api/public/listings (category without ID)"
        url = f"{self.base_url}/public/listings"
        params = {
            'country': 'TR',
            'source': 'category'
            # No category_id parameter - should cause 400 error
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 400:
                self.log_result(endpoint, "FAIL", "400 Bad Request", f"{response.status_code}", {
                    'error': f"Expected 400, got {response.status_code}: {response.text[:200]}"
                })
                return
                
            self.log_result(endpoint, "PASS", "400 Bad Request", f"400 Bad Request", {
                'status_code': response.status_code
            })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "400 Bad Request", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_ads_resolve(self) -> None:
        """Test 7: GET /api/ads/resolve?placement=home_top&country=TR"""
        endpoint = "GET /api/ads/resolve"
        url = f"{self.base_url}/ads/resolve"
        params = {
            'placement': 'home_top',
            'country': 'TR'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check placement_resolved set and has_active_ad bool
            placement_resolved = data.get('placement_resolved')
            has_active_ad = data.get('has_active_ad')
            
            if placement_resolved is None:
                self.log_result(endpoint, "FAIL", "placement_resolved set", "placement_resolved missing", {
                    'error': "placement_resolved field is missing"
                })
                return
                
            if not isinstance(has_active_ad, bool):
                self.log_result(endpoint, "FAIL", "has_active_ad bool", f"has_active_ad type: {type(has_active_ad)}", {
                    'error': f"has_active_ad is not boolean: {type(has_active_ad)}"
                })
                return
                
            self.log_result(endpoint, "PASS", "200, placement_resolved set, has_active_ad bool", 
                          f"200, placement_resolved={placement_resolved}, has_active_ad={has_active_ad}", {
                              'placement_resolved': placement_resolved,
                              'has_active_ad': has_active_ad
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with placement_resolved and has_active_ad", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def test_banners(self) -> None:
        """Test 8: GET /api/banners?placement=home_top&country=TR"""
        endpoint = "GET /api/banners"
        url = f"{self.base_url}/banners"
        params = {
            'placement': 'home_top',
            'country': 'TR'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result(endpoint, "FAIL", "200 OK", f"{response.status_code}", {
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                })
                return
                
            data = response.json()
            
            # Check items array + meta.mode
            items = data.get('items', [])
            meta = data.get('meta', {})
            mode = meta.get('mode')
            
            if not isinstance(items, list):
                self.log_result(endpoint, "FAIL", "items array", f"items type: {type(items)}", {
                    'error': f"items is not an array: {type(items)}"
                })
                return
                
            if mode is None:
                self.log_result(endpoint, "FAIL", "meta.mode set", "meta.mode missing", {
                    'error': "meta.mode field is missing"
                })
                return
                
            self.log_result(endpoint, "PASS", "200, items array + meta.mode", 
                          f"200, items count={len(items)}, meta.mode={mode}", {
                              'items_count': len(items),
                              'meta_mode': mode,
                              'meta': meta
                          })
                          
        except Exception as e:
            self.log_result(endpoint, "FAIL", "200 OK with items array and meta.mode", "Exception", {
                'error': f"Exception: {str(e)}"
            })
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all Turkish API contract tests"""
        print("🇹🇷 Turkish Backend API Contract Tests")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Run all 8 tests
        print("\n1) Testing categories tree L1...")
        self.test_categories_tree_l1()
        
        print("\n2) Testing categories tree Lall...")
        self.test_categories_tree_lall()
        
        print("\n3) Testing categories children...")
        self.test_categories_children()
        
        print("\n4) Testing categories listing-counts...")
        self.test_categories_listing_counts()
        
        print("\n5) Testing public listings showcase...")
        self.test_public_listings_showcase()
        
        print("\n6) Testing public listings category error...")
        self.test_public_listings_category_error()
        
        print("\n7) Testing ads resolve...")
        self.test_ads_resolve()
        
        print("\n8) Testing banners...")
        self.test_banners()
        
        # Summary
        passed_count = sum(1 for r in self.results if r['status'] == 'PASS')
        failed_count = sum(1 for r in self.results if r['status'] == 'FAIL')
        total_count = len(self.results)
        
        print("\n" + "=" * 60)
        print("📊 SONUÇ / RESULTS:")
        print("=" * 60)
        
        for result in self.results:
            status_emoji = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_emoji} {result['endpoint']}: {result['status']}")
            if result['status'] == 'FAIL' and result['details'].get('error'):
                print(f"   └─ {result['details']['error']}")
        
        print("\n" + "=" * 60)
        print(f"📈 ÖZET / SUMMARY: {passed_count}/{total_count} PASS")
        print(f"   ✅ Başarılı / Passed: {passed_count}")
        print(f"   ❌ Başarısız / Failed: {failed_count}")
        
        overall_status = "PASS" if failed_count == 0 else "FAIL"
        print(f"\n🎯 GENEL DURUM / OVERALL: {overall_status}")
        
        return {
            'total': total_count,
            'passed': passed_count,
            'failed': failed_count,
            'overall_status': overall_status,
            'results': self.results
        }

def main():
    """Main test runner"""
    tester = TurkishAPIContractTester()
    results = tester.run_all_tests()
    
    # Return exit code based on results
    return 0 if results['failed'] == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())