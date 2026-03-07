#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime

# Configuration from the review request
BASE_URL = "https://page-builder-stable.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"

class QuickBackendSanity:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        
    def authenticate(self):
        """Get admin access token"""
        login_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.access_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            print(f"✅ Admin authentication successful")
            return True
        else:
            print(f"❌ Admin authentication failed: {response.status_code}")
            return False
    
    def test_endpoint(self, method, endpoint, params=None, data=None, expect_status=None):
        """Test a single endpoint and return result"""
        try:
            if method.upper() == "GET":
                response = self.session.get(f"{API_BASE}{endpoint}", params=params)
            elif method.upper() == "POST":
                response = self.session.post(f"{API_BASE}{endpoint}", json=data, params=params)
            else:
                return f"❌ Unsupported method {method}"
            
            # Check for 5xx errors specifically
            if 500 <= response.status_code < 600:
                return f"❌ 5xx ERROR: {response.status_code}"
            
            # If specific status expected, check it
            if expect_status and response.status_code != expect_status:
                return f"⚠️ Expected {expect_status}, got {response.status_code}"
            
            # 2xx or 4xx are acceptable (no 5xx crashes)
            if 200 <= response.status_code < 500:
                return f"✅ {response.status_code} OK"
            
            return f"⚠️ Status {response.status_code}"
            
        except Exception as e:
            return f"❌ Exception: {str(e)}"

def main():
    print("🚀 Quick Backend Sanity - P1.1/P1.2/P2 Continuation")
    print("Target: https://page-builder-stable.preview.emergentagent.com")
    print("Credentials: admin@platform.com / Admin123!")
    print("=" * 60)
    
    tester = QuickBackendSanity()
    
    # Step 1: Authenticate
    if not tester.authenticate():
        print("❌ Cannot proceed without authentication")
        return 1
    
    print("\n📋 Testing specific endpoints from review request:")
    
    # Step 2: Test the exact endpoints mentioned in review request
    tests = [
        # 1. /api/admin/site/content-layout/bindings (this doesn't exist - expected 404)
        ("GET", "/admin/site/content-layout/bindings", None, None),
        
        # 2. /bindings/active (this needs parameters)
        ("GET", "/admin/site/content-layout/bindings/active", {
            "country": "DE", 
            "module": "real_estate", 
            "category_id": "12345678-1234-5678-9012-123456789012"
        }, None),
        
        # 3. /bindings/unbind (this is POST endpoint)
        ("POST", "/admin/site/content-layout/bindings/unbind", None, {
            "country": "DE",
            "module": "real_estate", 
            "category_id": "12345678-1234-5678-9012-123456789012"
        }),
        
        # 4. /api/site/content-layout/resolve for home
        ("GET", "/site/content-layout/resolve", {
            "page_type": "home",
            "country": "DE",
            "module": "global"
        }, None),
        
        # 5. /api/site/content-layout/resolve for search_l1  
        ("GET", "/site/content-layout/resolve", {
            "page_type": "search_l1",
            "country": "DE", 
            "module": "real_estate",
            "category_id": "12345678-1234-5678-9012-123456789012"
        }, None)
    ]
    
    results = []
    for method, endpoint, params, data in tests:
        print(f"\n{method} {endpoint}")
        if params:
            print(f"   Params: {params}")
        if data:
            print(f"   Data: {data}")
        
        result = tester.test_endpoint(method, endpoint, params, data)
        results.append((f"{method} {endpoint}", result))
        print(f"   {result}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    # Count results
    passed = len([r for _, r in results if r.startswith("✅")])
    failed = len([r for _, r in results if r.startswith("❌")])
    warnings = len([r for _, r in results if r.startswith("⚠️")])
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"⚠️ Warnings: {warnings}")
    print(f"❌ Failed: {failed}")
    
    # Check for 5xx specifically
    fivexx_errors = len([r for _, r in results if "5xx ERROR" in r])
    print(f"\n🔍 5xx Error Check: {'✅ PASS' if fivexx_errors == 0 else '❌ FAIL'} ({fivexx_errors} 5xx errors)")
    
    # Final verdict
    if fivexx_errors == 0:
        print(f"\n✅ OVERALL: PASS - No 5xx errors detected")
        return 0
    else:
        print(f"\n❌ OVERALL: FAIL - {fivexx_errors} 5xx errors found")
        return 1

if __name__ == "__main__":
    sys.exit(main())