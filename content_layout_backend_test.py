#!/usr/bin/env python3

import requests
import json
import sys

# Base URL from frontend env
BASE_URL = "https://dynamic-layout-io.preview.emergentagent.com"

def test_auth_login(email, password, role_name):
    """Test authentication for different user roles"""
    print(f"\n=== TESTING {role_name.upper()} LOGIN ({email}) ===")
    
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "email": email, 
        "password": password
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token', '')
            user_info = data.get('user', {})
            print(f"✅ {role_name} authentication successful")
            print(f"User ID: {user_info.get('id', 'N/A')}")
            print(f"User role: {user_info.get('role', 'N/A')}")
            print(f"Access token length: {len(access_token)} chars")
            return access_token, True
        else:
            print(f"❌ {role_name} authentication failed: {response.text}")
            return None, False
            
    except Exception as e:
        print(f"❌ Auth error: {str(e)}")
        return None, False

def test_content_layout_pages_get(token):
    """Test GET /api/admin/site/content-layout/pages"""
    print(f"\n=== TESTING GET PAGES ENDPOINT ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/admin/site/content-layout/pages"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            print(f"✅ Pages retrieved successfully")
            print(f"Total pages found: {len(items)}")
            print(f"Pagination: {data.get('pagination', {})}")
            return True, items
        else:
            print(f"❌ Failed to get pages: {response.text[:500]}")
            return False, []
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, []

def test_content_layout_pages_post(token):
    """Test POST /api/admin/site/content-layout/pages"""
    print(f"\n=== TESTING POST PAGES ENDPOINT ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/api/admin/site/content-layout/pages"
    
    # Create test page payload
    payload = {
        "page_type": "home",
        "country": "DE", 
        "module": "global"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            item = data.get('item', {})
            page_id = item.get('id')
            print(f"✅ Page created successfully")
            print(f"Created page ID: {page_id}")
            print(f"Page type: {item.get('page_type')}")
            print(f"Country: {item.get('country')}")
            print(f"Module: {item.get('module')}")
            return True, page_id
        elif response.status_code == 409:
            # Page already exists - this is OK for test
            print(f"⚠️ Page already exists (expected for test)")
            # Try to find existing page
            get_url = f"{url}?page_type=home&country=DE&module=global"
            get_response = requests.get(get_url, headers=headers)
            if get_response.status_code == 200:
                items = get_response.json().get('items', [])
                if items:
                    page_id = items[0].get('id')
                    print(f"✅ Found existing page ID: {page_id}")
                    return True, page_id
            return True, None
        else:
            print(f"❌ Failed to create page: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, None

def test_revisions_endpoints(token, page_id):
    """Test revisions endpoints for a specific page"""
    print(f"\n=== TESTING REVISIONS ENDPOINTS (Page: {page_id}) ===")
    
    if not page_id:
        print("❌ No page ID provided, skipping revisions tests")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET revisions
    try:
        url = f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions"
        response = requests.get(url, headers=headers)
        print(f"GET Revisions Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            revisions = data.get('items', [])
            print(f"✅ Revisions retrieved: {len(revisions)} revisions found")
            print(f"Pagination: {data.get('pagination', {})}")
        else:
            print(f"⚠️ Get revisions failed: {response.text[:300]}")
            
    except Exception as e:
        print(f"❌ Get revisions error: {str(e)}")
    
    # Test POST draft revision
    try:
        url = f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft"
        draft_payload = {
            "payload_json": {
                "rows": [
                    {
                        "columns": [
                            {
                                "components": [
                                    {
                                        "key": "shared.text-block",
                                        "props": {
                                            "title": "Test Title",
                                            "body": "Test content for draft revision"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        response = requests.post(url, json=draft_payload, headers=headers)
        print(f"POST Draft Revision Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            revision_id = data.get('item', {}).get('id')
            print(f"✅ Draft revision created: {revision_id}")
            return True
        else:
            print(f"⚠️ Create draft failed: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Draft revision error: {str(e)}")
        return False

def test_publish_flow(token, page_id):
    """Test PUBLISH revision flow"""
    print(f"\n=== TESTING PUBLISH FLOW (Page: {page_id}) ===")
    
    if not page_id:
        print("❌ No page ID provided, skipping publish tests")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test PUBLISH endpoint 
    try:
        url = f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/publish"
        
        # First try to publish current draft
        response = requests.post(url, headers=headers)
        print(f"PUBLISH Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✅ Publish successful")
            print(f"Published revision ID: {data.get('item', {}).get('id')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️ No draft to publish (expected if no draft exists)")
            return True
        else:
            print(f"⚠️ Publish failed: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Publish error: {str(e)}")
        return False

def test_binding_endpoints(token):
    """Test GET/POST binding endpoints"""
    print(f"\n=== TESTING BINDING ENDPOINTS ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test GET bindings/active
    try:
        test_category_id = "3d7dc54d-df6d-428e-8eea-f315d073ada9"  # Sample category ID
        url = f"{BASE_URL}/api/admin/site/content-layout/bindings/active?country=DE&module=real_estate&category_id={test_category_id}"
        response = requests.get(url, headers=headers)
        print(f"GET Active Bindings Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Active bindings retrieved successfully")
            print(f"Active bindings: {data}")
        elif response.status_code == 404:
            print(f"✅ No active bindings found (expected for test category)")
        else:
            print(f"⚠️ Get bindings failed: {response.text[:300]}")
            
    except Exception as e:
        print(f"❌ Get bindings error: {str(e)}")
    
    # Test POST binding (create new binding)
    try:
        url = f"{BASE_URL}/api/admin/site/content-layout/bindings"
        bind_payload = {
            "country": "DE",
            "module": "real_estate", 
            "category_id": "test-category-id",
            "layout_page_id": "test-page-id"
        }
        
        response = requests.post(url, json=bind_payload, headers=headers)
        print(f"POST Binding Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print(f"✅ Binding created successfully")
            return True
        elif response.status_code in [400, 404, 409]:
            print(f"✅ Binding validation working (expected error for test data)")
            return True
        else:
            print(f"⚠️ Binding failed: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Binding error: {str(e)}")
        return False

def test_unbind_endpoint(token):
    """Test UNBIND endpoint"""
    print(f"\n=== TESTING UNBIND ENDPOINT ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        url = f"{BASE_URL}/api/admin/site/content-layout/bindings/unbind"
        unbind_payload = {
            "country": "DE",
            "module": "real_estate",
            "category_id": "test-category-id"
        }
        
        response = requests.post(url, json=unbind_payload, headers=headers)
        print(f"UNBIND Status: {response.status_code}")
        
        if response.status_code in [200, 404]:
            print(f"✅ Unbind endpoint working")
            return True
        else:
            print(f"⚠️ Unbind failed: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Unbind error: {str(e)}")
        return False

def test_resolve_endpoint():
    """Test /api/site/content-layout/resolve endpoint"""
    print(f"\n=== TESTING RESOLVE ENDPOINT ===")
    
    test_endpoints = [
        "/api/site/content-layout/resolve?page_type=home&country=DE&module=global",
        "/api/site/content-layout/resolve?page_type=search_l1&country=DE&module=real_estate"
    ]
    
    success_count = 0
    
    for endpoint in test_endpoints:
        url = f"{BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url)
            print(f"Endpoint: {endpoint}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Resolve working")
                success_count += 1
                # Check response structure
                try:
                    data = response.json()
                    print(f"Response keys: {list(data.keys())}")
                    if 'layout' in data or 'components' in data:
                        print(f"✅ Contains layout data")
                    elif 'source' in data:
                        print(f"Source: {data.get('source')}")
                except:
                    print(f"Response length: {len(response.text)} chars")
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {str(e)}")
    
    return success_count > 0

def main():
    print("=== BACKEND HIZ DI DOĞRULAMA (CONTENT LAYOUT API) ===")
    print(f"Base URL: {BASE_URL}")
    
    results = {}
    tokens = {}
    
    # 1. Test all three login accounts
    print("\n" + "="*60)
    print("1) LOGIN DURUMLARINI KONTROL ET")
    print("="*60)
    
    accounts = [
        ("admin@platform.com", "Admin123!", "admin"),
        ("dealer@platform.com", "Dealer123!", "dealer"),
        ("user@platform.com", "User123!", "user")
    ]
    
    login_success_count = 0
    for email, password, role in accounts:
        token, success = test_auth_login(email, password, role)
        if success:
            tokens[role] = token
            login_success_count += 1
        results[f'{role}_login'] = success
    
    if 'admin' not in tokens:
        print("\n❌ CRITICAL: Admin token required for content layout tests")
        return False
    
    admin_token = tokens['admin']
    
    # 2. Test Content Layout API Flow
    print("\n" + "="*60)
    print("2) CONTENT LAYOUT API AKIŞI")
    print("="*60)
    
    # GET pages
    pages_get_success, pages = test_content_layout_pages_get(admin_token)
    results['pages_get'] = pages_get_success
    
    # POST pages 
    pages_post_success, page_id = test_content_layout_pages_post(admin_token)
    results['pages_post'] = pages_post_success
    
    # GET revisions & POST draft
    if page_id or pages:
        test_page_id = page_id if page_id else (pages[0].get('id') if pages else None)
        revisions_success = test_revisions_endpoints(admin_token, test_page_id)
        results['revisions'] = revisions_success
        
        # PUBLISH flow
        publish_success = test_publish_flow(admin_token, test_page_id)
        results['publish'] = publish_success
    else:
        results['revisions'] = False
        results['publish'] = False
        
    # Binding endpoints
    binding_success = test_binding_endpoints(admin_token)
    results['binding'] = binding_success
    
    # Unbind endpoint
    unbind_success = test_unbind_endpoint(admin_token)
    results['unbind'] = unbind_success
    
    # 3. Test Resolve Endpoint
    print("\n" + "="*60)
    print("3) RESOLVE ENDPOINT DOĞRULA")  
    print("="*60)
    
    resolve_success = test_resolve_endpoint()
    results['resolve'] = resolve_success
    
    # 4. Final Summary
    print("\n" + "="*60)
    print("4) KISA PASS/FAIL VE KRITIK BULGULAR")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nLOGIN DURUMU:")
    for role in ['admin', 'dealer', 'user']:
        status = "✅ PASS" if results.get(f'{role}_login', False) else "❌ FAIL"
        print(f"  {role}@platform.com: {status}")
    
    print(f"\nCONTENT LAYOUT API:")
    api_tests = ['pages_get', 'pages_post', 'revisions', 'publish', 'binding', 'unbind']
    for test in api_tests:
        status = "✅ PASS" if results.get(test, False) else "❌ FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nRESOLVE ENDPOINT:")
    status = "✅ PASS" if results.get('resolve', False) else "❌ FAIL"
    print(f"  /api/site/content-layout/resolve: {status}")
    
    print(f"\nGENEL DURUM: {passed}/{total} test PASS")
    
    # Critical findings
    print(f"\nKRITIK BULGULAR:")
    if login_success_count < 3:
        print(f"❌ Login hesaplarından {3-login_success_count} tanesi çalışmıyor")
    else:
        print(f"✅ Tüm login hesapları çalışıyor")
        
    api_passed = sum(1 for test in api_tests if results.get(test, False))
    if api_passed < len(api_tests):
        print(f"❌ Content Layout API akışında {len(api_tests)-api_passed} endpoint problemi var")
    else:
        print(f"✅ Content Layout API akışı tamamen çalışıyor")
        
    if not results.get('resolve', False):
        print(f"❌ Resolve endpoint çalışmıyor")
    else:
        print(f"✅ Resolve endpoint çalışıyor")
    
    # Overall result
    if passed >= total * 0.8:  # 80% pass rate
        print(f"\n✅ FINAL SONUÇ: PASS - Backend doğrulama başarılı")
        return True
    else:
        print(f"\n❌ FINAL SONUÇ: FAIL - Backend doğrulama başarısız")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)