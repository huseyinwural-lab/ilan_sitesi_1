#!/usr/bin/env python3

"""
Category Backend API Validation - Turkish Review Request  
Testing category deletion cascade functionality and error handling.

Review Request: "Kategori tarafı için backend hedefli doğrulama yap."
Base URL: https://builder-hub-151.preview.emergentagent.com
Hesap: admin@platform.com / Admin123!

Testler:
1) DELETE /api/admin/categories/{category_id}?cascade=true
   - parent+child oluşturup parent sil
   - response'da deleted_count ve deleted_descendant_count alanları dönüyor mu
   - child da siliniyor mu doğrula

2) DELETE invalid id
   - /api/admin/categories/not-a-valid-id çağır
   - 400 ve structured detail dönmeli:
     - error_code=CATEGORY_ID_INVALID
     - field_name=category_id

3) Kategori create/update hatalarında detail yapısı
   - slug conflict veya uygun bir conflict tetikle
   - detail içinde error_code, field_name gibi alanların döndüğünü doğrula

PASS/FAIL kısa rapor ver.
"""

import requests
import json
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


class CategoryBackendTester:
    def __init__(self):
        self.base_url = "https://builder-hub-151.preview.emergentagent.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Category-Backend-Tester/1.0'
        })
        self.results = []
        self.passed = 0
        self.failed = 0
        
        # Admin credentials
        self.admin_credentials = {
            "email": "admin@platform.com",
            "password": "Admin123!"
        }
        self.auth_token = None
        
        # Store created category IDs for cleanup
        self.created_categories = []

    def authenticate_admin(self) -> bool:
        """Authenticate as admin"""
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

    def create_category(self, name: str, slug: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a test category and return its ID"""
        print(f"\n📝 Creating test category: {name} (slug: {slug})")
        
        payload = {
            "country_code": "TR",
            "module": "vehicle",
            "name": name,  # Use direct name field instead of translations
            "slug": slug,
            "sort_order": 1,
            "is_enabled": True
        }
        
        if parent_id:
            payload["parent_id"] = parent_id
        
        try:
            url = f"{self.base_url}/admin/categories"
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                category_id = data.get('category', {}).get('id')
                if category_id:
                    self.created_categories.append(category_id)
                    print(f"✅ Created category ID: {category_id}")
                    return category_id
                else:
                    print(f"❌ No category ID in response: {data}")
                    return None
            else:
                print(f"❌ Category creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Category creation error: {e}")
            return None

    def test_cascade_delete(self) -> Dict[str, Any]:
        """Test 1: DELETE with cascade=true - parent+child deletion"""
        print(f"\n{'='*60}")
        print("🧪 TEST 1: CASCADE DELETE (Parent + Child)")
        print(f"{'='*60}")
        
        # Create parent category
        parent_slug = f"test-parent-{uuid.uuid4().hex[:8]}"
        parent_id = self.create_category("Test Parent Category", parent_slug)
        
        if not parent_id:
            return {
                'test': 'cascade_delete',
                'success': False,
                'error': 'Failed to create parent category'
            }
        
        # Create child category
        child_slug = f"test-child-{uuid.uuid4().hex[:8]}"
        child_id = self.create_category("Test Child Category", child_slug, parent_id)
        
        if not child_id:
            return {
                'test': 'cascade_delete',
                'success': False,
                'error': 'Failed to create child category'
            }
        
        print(f"\n🎯 Testing DELETE /admin/categories/{parent_id}?cascade=true")
        
        try:
            url = f"{self.base_url}/admin/categories/{parent_id}?cascade=true"
            response = self.session.delete(url, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"🔍 Response Data: {json.dumps(data, indent=2)}")
                
                # Check required fields
                checks = {
                    'deleted_count': 'deleted_count' in data,
                    'deleted_descendant_count': 'deleted_descendant_count' in data,
                    'cascade_flag': data.get('cascade') == True,
                    'deleted_count_value': data.get('deleted_count', 0) >= 2,  # Parent + child
                    'descendant_count_value': data.get('deleted_descendant_count', 0) >= 1  # Child
                }
                
                all_passed = all(checks.values())
                
                for check, passed in checks.items():
                    icon = "✅" if passed else "❌"
                    print(f"   {icon} {check}: {passed}")
                
                if all_passed:
                    print("✅ CASCADE DELETE: PASS")
                    self.passed += 1
                    
                    # Verify child is also deleted by trying to get it
                    child_check_url = f"{self.base_url}/admin/categories?country=TR&module=vehicle"
                    child_response = self.session.get(child_check_url, timeout=30)
                    
                    if child_response.status_code == 200:
                        categories = child_response.json().get('categories', [])
                        child_found = any(cat.get('id') == child_id for cat in categories if not cat.get('is_deleted'))
                        
                        if not child_found:
                            print("✅ Child category confirmed deleted")
                        else:
                            print("❌ Child category still exists (not properly deleted)")
                            all_passed = False
                            self.failed += 1
                    
                    return {
                        'test': 'cascade_delete',
                        'success': all_passed,
                        'parent_id': parent_id,
                        'child_id': child_id,
                        'deleted_count': data.get('deleted_count'),
                        'deleted_descendant_count': data.get('deleted_descendant_count'),
                        'response_data': data
                    }
                else:
                    print("❌ CASCADE DELETE: FAIL")
                    self.failed += 1
                    return {
                        'test': 'cascade_delete',
                        'success': False,
                        'error': 'Missing required response fields',
                        'checks': checks,
                        'response_data': data
                    }
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw error: {response.text[:200]}")
                
                self.failed += 1
                return {
                    'test': 'cascade_delete',
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            print(f"❌ Network error: {e}")
            self.failed += 1
            return {
                'test': 'cascade_delete',
                'success': False,
                'error': str(e)
            }

    def test_invalid_category_id(self) -> Dict[str, Any]:
        """Test 2: DELETE with invalid category ID"""
        print(f"\n{'='*60}")
        print("🧪 TEST 2: INVALID CATEGORY ID")
        print(f"{'='*60}")
        
        invalid_id = "not-a-valid-id"
        url = f"{self.base_url}/admin/categories/{invalid_id}"
        
        print(f"🎯 Testing DELETE {url}")
        
        try:
            response = self.session.delete(url, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 400:
                try:
                    data = response.json()
                    print(f"🔍 Response Data: {json.dumps(data, indent=2)}")
                    
                    # Check error structure
                    detail = data.get('detail', {})
                    checks = {
                        'status_400': True,
                        'has_detail': isinstance(detail, dict),
                        'error_code': detail.get('error_code') == 'CATEGORY_ID_INVALID',
                        'field_name': detail.get('field_name') == 'category_id'
                    }
                    
                    all_passed = all(checks.values())
                    
                    for check, passed in checks.items():
                        icon = "✅" if passed else "❌"
                        print(f"   {icon} {check}: {passed}")
                    
                    if all_passed:
                        print("✅ INVALID ID TEST: PASS")
                        self.passed += 1
                    else:
                        print("❌ INVALID ID TEST: FAIL")
                        self.failed += 1
                    
                    return {
                        'test': 'invalid_category_id',
                        'success': all_passed,
                        'checks': checks,
                        'response_data': data
                    }
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    self.failed += 1
                    return {
                        'test': 'invalid_category_id',
                        'success': False,
                        'error': 'Invalid JSON response',
                        'raw_response': response.text
                    }
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                self.failed += 1
                return {
                    'test': 'invalid_category_id',
                    'success': False,
                    'error': f'Expected 400, got {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            print(f"❌ Network error: {e}")
            self.failed += 1
            return {
                'test': 'invalid_category_id',
                'success': False,
                'error': str(e)
            }

    def test_create_slug_conflict(self) -> Dict[str, Any]:
        """Test 3: Create category with slug conflict"""
        print(f"\n{'='*60}")
        print("🧪 TEST 3: SLUG CONFLICT ERROR STRUCTURE")
        print(f"{'='*60}")
        
        # First, create a category
        test_slug = f"conflict-test-{uuid.uuid4().hex[:8]}"
        first_category_id = self.create_category("First Category", test_slug)
        
        if not first_category_id:
            return {
                'test': 'slug_conflict',
                'success': False,
                'error': 'Failed to create first category for conflict test'
            }
        
        # Now try to create another category with the same slug
        print(f"\n🎯 Attempting to create duplicate slug: {test_slug}")
        
        payload = {
            "country_code": "TR",
            "module": "vehicle",
            "name": "Duplicate Slug Category",  # Use direct name field
            "slug": test_slug,  # Same slug - should cause conflict
            "sort_order": 2,
            "is_enabled": True
        }
        
        try:
            url = f"{self.base_url}/admin/categories"
            response = self.session.post(url, json=payload, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 400 or response.status_code == 409:
                try:
                    data = response.json()
                    print(f"🔍 Response Data: {json.dumps(data, indent=2)}")
                    
                    # Check error structure
                    detail = data.get('detail', {})
                    checks = {
                        'status_4xx': response.status_code in [400, 409],
                        'has_detail': isinstance(detail, dict),
                        'has_error_code': 'error_code' in detail,
                        'has_field_name': 'field_name' in detail,
                        'slug_related': detail.get('field_name') == 'slug' or 'slug' in detail.get('error_code', '').lower()
                    }
                    
                    all_passed = all(checks.values())
                    
                    for check, passed in checks.items():
                        icon = "✅" if passed else "❌"
                        print(f"   {icon} {check}: {passed}")
                    
                    if all_passed:
                        print("✅ SLUG CONFLICT TEST: PASS")
                        self.passed += 1
                    else:
                        print("❌ SLUG CONFLICT TEST: FAIL")
                        self.failed += 1
                    
                    return {
                        'test': 'slug_conflict',
                        'success': all_passed,
                        'checks': checks,
                        'response_data': data,
                        'first_category_id': first_category_id
                    }
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    self.failed += 1
                    return {
                        'test': 'slug_conflict',
                        'success': False,
                        'error': 'Invalid JSON response',
                        'raw_response': response.text
                    }
            else:
                print(f"❌ Expected 400/409, got {response.status_code}")
                self.failed += 1
                return {
                    'test': 'slug_conflict',
                    'success': False,
                    'error': f'Expected 400/409, got {response.status_code}',
                    'response': response.text
                }
                
        except Exception as e:
            print(f"❌ Network error: {e}")
            self.failed += 1
            return {
                'test': 'slug_conflict',
                'success': False,
                'error': str(e)
            }

    def cleanup_created_categories(self):
        """Clean up any test categories that were created"""
        if not self.created_categories:
            return
            
        print(f"\n🧹 Cleaning up {len(self.created_categories)} test categories...")
        
        for category_id in self.created_categories:
            try:
                url = f"{self.base_url}/admin/categories/{category_id}?cascade=true"
                response = self.session.delete(url, timeout=30)
                if response.status_code == 200:
                    print(f"   ✅ Deleted {category_id}")
                else:
                    print(f"   ⚠️ Could not delete {category_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Error deleting {category_id}: {e}")

    def run_category_tests(self):
        """Run all category backend tests"""
        print("🏁 CATEGORY BACKEND VALIDATION")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Focus: Turkish Review Request - Category Backend Testing")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Authenticate admin
        if not self.authenticate_admin():
            print("❌ Admin authentication failed - cannot continue")
            return False

        # Run tests
        test1_result = self.test_cascade_delete()
        test2_result = self.test_invalid_category_id()
        test3_result = self.test_create_slug_conflict()
        
        self.results = [test1_result, test2_result, test3_result]
        
        # Cleanup
        self.cleanup_created_categories()
        
        return True

    def print_summary(self):
        """Print comprehensive test summary"""
        total_tests = 3
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print("🏁 CATEGORY BACKEND TEST SUMMARY")
        print(f"{'='*60}")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        test_names = {
            'cascade_delete': '1) CASCADE DELETE (parent+child deletion)',
            'invalid_category_id': '2) INVALID ID ERROR HANDLING',
            'slug_conflict': '3) SLUG CONFLICT ERROR STRUCTURE'
        }
        
        for result in self.results:
            test_key = result.get('test', 'unknown')
            test_name = test_names.get(test_key, test_key)
            success = result.get('success', False)
            status_icon = "✅" if success else "❌"
            
            print(f"{status_icon} {test_name}")
            
            if success and test_key == 'cascade_delete':
                deleted_count = result.get('deleted_count', 0)
                descendant_count = result.get('deleted_descendant_count', 0)
                print(f"   📊 Deleted: {deleted_count} total, {descendant_count} descendants")
            
            if not success and 'error' in result:
                print(f"   ⚠️ Error: {result['error']}")

        # Final verdict
        print(f"\n🎯 FINAL VERDICT:")
        if self.failed == 0:
            print(f"✅ ALL TESTS PASSED")
            print(f"🚀 All {self.passed} category backend tests working correctly")
            print(f"🔥 Category backend validation: SUCCESSFUL")
        else:
            print(f"❌ {self.failed}/{total_tests} TESTS FAILED") 
            print(f"⚠️ Category backend validation: REQUIRES ATTENTION")
        
        # Kısa PASS/FAIL as requested
        verdict = "PASS" if self.failed == 0 else "FAIL"
        print(f"\n🏆 Kısa PASS/FAIL Raporu: {verdict}")
        
        return self.failed == 0


def main():
    """Main execution function"""
    tester = CategoryBackendTester()
    
    try:
        # Run the category backend tests
        if not tester.run_category_tests():
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
        sys.exit(1)


if __name__ == "__main__":
    main()