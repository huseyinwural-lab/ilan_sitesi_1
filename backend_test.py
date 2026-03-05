#!/usr/bin/env python3

"""
Backend endpoint testing script for reviewing new endpoints.
Tests the following Turkish review request endpoints:

1. /api/v1/listings/vehicle/{id} - seller.rating, seller.reviews_count, seller.response_rate
2. /api/v1/listings/vehicle/{id}/similar - score, score_explanation, score_breakdown
3. /api/public/geo/nearby-pois - 200 with items (source osm/fallback)
4. /api/admin/site/content-layout/revisions/{id}/policy-report - checks[].fix_suggestion + suggested_fixes
5. /api/admin/site/content-layout/revisions/{id}/policy-autofix - 200 + report_after
"""

import os
import sys
import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Set up environment path
sys.path.append('/app/backend')

def load_backend_url() -> str:
    """Load backend URL from frontend .env file"""
    frontend_env_path = "/app/frontend/.env"
    backend_url = "https://content-canvas-17.preview.emergentagent.com"  # fallback
    
    try:
        with open(frontend_env_path, 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_url = line.split('=', 1)[1].strip()
                    break
    except Exception as e:
        print(f"Warning: Could not read frontend .env file: {e}")
    
    return f"{backend_url}/api" if not backend_url.endswith('/api') else backend_url

class BackendTester:
    def __init__(self):
        self.base_url = load_backend_url()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Backend-Tester/1.0'
        })
        self.admin_token = None
        self.results = {
            'tests': [],
            'passed': 0,
            'failed': 0,
            'total': 0
        }
        
    def log_result(self, endpoint: str, status: str, details: Dict[str, Any]):
        """Log test result"""
        self.results['tests'].append({
            'endpoint': endpoint,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details
        })
        if status == 'PASS':
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
        self.results['total'] += 1
        
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {endpoint}: {status}")
        if details.get('error'):
            print(f"   Error: {details['error']}")
        elif details.get('response_status'):
            print(f"   Status: {details['response_status']}")

    def login_admin(self) -> bool:
        """Login as admin user and get access token"""
        login_url = f"{self.base_url}/auth/login"
        payload = {
            "email": "admin@platform.com",
            "password": "Admin123!"
        }
        
        try:
            response = self.session.post(login_url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get('access_token')
                if self.admin_token:
                    self.session.headers['Authorization'] = f'Bearer {self.admin_token}'
                    print("✅ Admin login successful")
                    return True
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return False

    def get_test_vehicle_listing_id(self) -> Optional[str]:
        """Get a test vehicle listing ID from search results or use known ID"""
        # Try search first
        try:
            search_url = f"{self.base_url}/public/search"
            params = {
                'module': 'vehicle',
                'limit': 1
            }
            response = self.session.get(search_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                if results and len(results) > 0:
                    listing_id = results[0].get('id')
                    print(f"Found test vehicle listing ID: {listing_id}")
                    return listing_id
        except Exception as e:
            print(f"Error searching for vehicle listing: {e}")
        
        # Fall back to known listing ID from backend logs
        known_listing_id = "8964bb00-7612-455e-be2e-6d39f94ac9af"
        print(f"Using known vehicle listing ID: {known_listing_id}")
        return known_listing_id

    def get_test_revision_id(self) -> Optional[str]:
        """Get a test layout revision ID"""
        if not self.admin_token:
            return None
            
        try:
            # First get a layout page 
            pages_url = f"{self.base_url}/admin/site/content-layout/pages"
            response = self.session.get(pages_url, params={'limit': 1})
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get('items', [])
                if pages:
                    page_id = pages[0]['id']
                    # Get revisions for this page
                    revisions_url = f"{self.base_url}/admin/site/content-layout/pages/{page_id}/revisions"
                    rev_response = self.session.get(revisions_url)
                    
                    if rev_response.status_code == 200:
                        rev_data = rev_response.json()
                        revisions = rev_data.get('items', [])
                        if revisions:
                            revision_id = revisions[0]['id']
                            print(f"Found test revision ID: {revision_id}")
                            return revision_id
                        else:
                            # Create a draft revision if none exist
                            draft_url = f"{self.base_url}/admin/site/content-layout/pages/{page_id}/revisions/draft"
                            draft_payload = {
                                "payload_json": {
                                    "rows": [
                                        {
                                            "id": "test-row-1",
                                            "columns": [
                                                {
                                                    "id": "test-col-1",
                                                    "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                                                    "components": [
                                                        {
                                                            "id": "test-default-content",
                                                            "key": "listing.create.default-content",
                                                            "props": {}
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                            draft_response = self.session.post(draft_url, json=draft_payload)
                            if draft_response.status_code == 200:
                                draft_data = draft_response.json()
                                revision_id = draft_data.get('item', {}).get('id')
                                print(f"Created test revision ID: {revision_id}")
                                return revision_id
            
            print("No layout pages or revisions found")
            return None
        except Exception as e:
            print(f"Error finding test revision: {e}")
            return None

    def test_vehicle_listing_seller_fields(self) -> None:
        """Test 1: /api/v1/listings/vehicle/{id} for seller fields"""
        listing_id = self.get_test_vehicle_listing_id()
        if not listing_id:
            self.log_result("/v1/listings/vehicle/{id}", "FAIL", {
                "error": "No test vehicle listing found",
                "expected_fields": ["seller.rating", "seller.reviews_count", "seller.response_rate"]
            })
            return
            
        url = f"{self.base_url}/v1/listings/vehicle/{listing_id}"
        
        try:
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.log_result("/v1/listings/vehicle/{id}", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text[:200]
                })
                return
                
            data = response.json()
            seller = data.get('seller', {})
            
            # Check required seller fields
            required_fields = ['rating', 'reviews_count', 'response_rate']
            missing_fields = []
            present_fields = {}
            
            for field in required_fields:
                if field in seller:
                    present_fields[field] = seller[field]
                else:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_result("/v1/listings/vehicle/{id}", "FAIL", {
                    "error": f"Missing seller fields: {missing_fields}",
                    "present_fields": present_fields,
                    "response_status": response.status_code
                })
            else:
                self.log_result("/v1/listings/vehicle/{id}", "PASS", {
                    "seller_fields": present_fields,
                    "response_status": response.status_code
                })
                
        except Exception as e:
            self.log_result("/v1/listings/vehicle/{id}", "FAIL", {
                "error": f"Exception: {str(e)}"
            })

    def test_vehicle_listing_similar(self) -> None:
        """Test 2: /api/v1/listings/vehicle/{id}/similar for score fields"""
        listing_id = self.get_test_vehicle_listing_id()
        if not listing_id:
            self.log_result("/v1/listings/vehicle/{id}/similar", "FAIL", {
                "error": "No test vehicle listing found",
                "expected_fields": ["score", "score_explanation", "score_breakdown"]
            })
            return
            
        url = f"{self.base_url}/v1/listings/vehicle/{listing_id}/similar"
        
        try:
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.log_result("/v1/listings/vehicle/{id}/similar", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text[:200]
                })
                return
                
            data = response.json()
            results = data.get('results', []) or data.get('items', [])
            
            if not results:
                self.log_result("/v1/listings/vehicle/{id}/similar", "FAIL", {
                    "error": "No similar listings returned",
                    "response_status": response.status_code,
                    "response_keys": list(data.keys()) if data else []
                })
                return
            
            # Check score fields in first result
            first_result = results[0]
            required_fields = ['score', 'score_explanation', 'score_breakdown']
            missing_fields = []
            present_fields = {}
            
            for field in required_fields:
                if field in first_result:
                    present_fields[field] = first_result[field]
                else:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log_result("/v1/listings/vehicle/{id}/similar", "FAIL", {
                    "error": f"Missing score fields: {missing_fields}",
                    "present_fields": present_fields,
                    "total_results": len(results),
                    "response_status": response.status_code
                })
            else:
                self.log_result("/v1/listings/vehicle/{id}/similar", "PASS", {
                    "score_fields": present_fields,
                    "total_results": len(results),
                    "response_status": response.status_code
                })
                
        except Exception as e:
            self.log_result("/v1/listings/vehicle/{id}/similar", "FAIL", {
                "error": f"Exception: {str(e)}"
            })

    def test_nearby_pois(self) -> None:
        """Test 3: /api/public/geo/nearby-pois for 200 status and items"""
        url = f"{self.base_url}/public/geo/nearby-pois"
        params = {
            'lat': '52.5200',  # Berlin coordinates
            'lng': '13.4050',
            'radius': '1000'
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code != 200:
                self.log_result("/public/geo/nearby-pois", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text[:200]
                })
                return
                
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                self.log_result("/public/geo/nearby-pois", "FAIL", {
                    "error": "No POI items returned",
                    "response_data": data,
                    "response_status": response.status_code
                })
                return
            
            # Check for source field (osm/fallback)
            sources_found = set()
            for item in items[:5]:  # Check first 5 items
                source = item.get('source')
                if source:
                    sources_found.add(source)
            
            self.log_result("/public/geo/nearby-pois", "PASS", {
                "items_count": len(items),
                "sources_found": list(sources_found),
                "response_status": response.status_code
            })
                
        except Exception as e:
            self.log_result("/public/geo/nearby-pois", "FAIL", {
                "error": f"Exception: {str(e)}"
            })

    def test_policy_report(self) -> None:
        """Test 4: /api/admin/site/content-layout/revisions/{id}/policy-report"""
        revision_id = self.get_test_revision_id()
        if not revision_id:
            self.log_result("/admin/site/content-layout/revisions/{id}/policy-report", "FAIL", {
                "error": "No test revision found"
            })
            return
            
        url = f"{self.base_url}/admin/site/content-layout/revisions/{revision_id}/policy-report"
        
        try:
            response = self.session.get(url)
            
            if response.status_code != 200:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-report", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text[:200]
                })
                return
                
            data = response.json()
            report = data.get('report', {})
            
            # Check for required fields in policy report
            checks = report.get('checks', [])
            suggested_fixes = report.get('suggested_fixes', [])
            
            # Check if checks have fix_suggestion
            fix_suggestions_found = []
            for check in checks:
                if 'fix_suggestion' in check and check['fix_suggestion']:
                    fix_suggestions_found.append(check['fix_suggestion'])
            
            if not checks:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-report", "FAIL", {
                    "error": "No checks found in policy report",
                    "report_keys": list(report.keys()),
                    "response_status": response.status_code
                })
            elif not fix_suggestions_found and not suggested_fixes:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-report", "FAIL", {
                    "error": "No fix_suggestions found in checks or suggested_fixes field",
                    "checks_count": len(checks),
                    "suggested_fixes": suggested_fixes,
                    "response_status": response.status_code
                })
            else:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-report", "PASS", {
                    "checks_count": len(checks),
                    "fix_suggestions_in_checks": len(fix_suggestions_found),
                    "suggested_fixes_count": len(suggested_fixes),
                    "response_status": response.status_code
                })
                
        except Exception as e:
            self.log_result("/admin/site/content-layout/revisions/{id}/policy-report", "FAIL", {
                "error": f"Exception: {str(e)}"
            })

    def test_policy_autofix(self) -> None:
        """Test 5: /api/admin/site/content-layout/revisions/{id}/policy-autofix"""
        revision_id = self.get_test_revision_id()
        if not revision_id:
            self.log_result("/admin/site/content-layout/revisions/{id}/policy-autofix", "FAIL", {
                "error": "No test revision found"
            })
            return
            
        url = f"{self.base_url}/admin/site/content-layout/revisions/{revision_id}/policy-autofix"
        
        try:
            response = self.session.post(url, json={})
            
            if response.status_code != 200:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-autofix", "FAIL", {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text[:200]
                })
                return
                
            data = response.json()
            
            # Check for report_after field
            report_after = data.get('report_after')
            if not report_after:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-autofix", "FAIL", {
                    "error": "Missing report_after field",
                    "response_keys": list(data.keys()),
                    "response_status": response.status_code
                })
            else:
                self.log_result("/admin/site/content-layout/revisions/{id}/policy-autofix", "PASS", {
                    "has_report_after": True,
                    "auto_fix_actions": data.get('auto_fix_actions', []),
                    "response_status": response.status_code
                })
                
        except Exception as e:
            self.log_result("/admin/site/content-layout/revisions/{id}/policy-autofix", "FAIL", {
                "error": f"Exception: {str(e)}"
            })

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print(f"\n🚀 Starting backend endpoint tests...")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Login as admin first
        if not self.login_admin():
            print("❌ Failed to login as admin - some tests may fail")
        
        # Run all tests
        self.test_vehicle_listing_seller_fields()
        self.test_vehicle_listing_similar()  
        self.test_nearby_pois()
        self.test_policy_report()
        self.test_policy_autofix()
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results Summary:")
        print(f"   Total: {self.results['total']}")
        print(f"   Passed: {self.results['passed']} ✅")
        print(f"   Failed: {self.results['failed']} ❌")
        
        return self.results

def main():
    """Main test runner"""
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Print summary for Turkish review request
    print(f"\n🇹🇷 Turkish Review Request Summary:")
    print("=" * 60)
    
    for test in results['tests']:
        endpoint = test['endpoint']
        status = test['status']
        status_text = "PASS" if status == "PASS" else "FAIL"
        
        if "/v1/listings/vehicle/" in endpoint and "/similar" not in endpoint:
            print(f"1) {endpoint} → seller fields: {status_text}")
        elif "/v1/listings/vehicle/" in endpoint and "/similar" in endpoint:
            print(f"2) {endpoint} → score fields: {status_text}")
        elif "/public/geo/nearby-pois" in endpoint:
            print(f"3) {endpoint} → 200 + items: {status_text}")
        elif "policy-report" in endpoint:
            print(f"4) {endpoint} → checks + fixes: {status_text}")
        elif "policy-autofix" in endpoint:
            print(f"5) {endpoint} → 200 + report_after: {status_text}")
    
    overall_status = "PASS" if results['failed'] == 0 else "FAIL"
    print(f"\n📝 Kısa PASS/FAIL özeti: {overall_status}")
    
    return 0 if results['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())