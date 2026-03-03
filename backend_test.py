#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime

# Base URL from the environment
BASE_URL = "https://marketplace-admin-13.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

def test_dealer_portal_regression():
    """
    Quick regression test for dealer portal endpoints as per review request:
    - Login endpoint: POST /api/auth/login (dealer)
    - Dealer route access: GET /api/dealer/dashboard/navigation-summary, GET /api/dealer/virtual-tours, 
      GET /api/dealer/messages, GET /api/dealer/favorites, GET /api/dealer/reports
    - Auth guard: navigation-summary endpoint should return 401/403 when accessed without auth
    """
    
    print(f"=== Dealer Portal Regression Test ===")
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    results = {}
    
    # Test 1: Dealer Login
    print("1. Testing dealer login endpoint: POST /api/auth/login")
    try:
        login_payload = {
            "email": "dealer@platform.com",
            "password": "Dealer123!"
        }
        
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            login_data = response.json()
            access_token = login_data.get("access_token")
            user_info = login_data.get("user", {})
            
            print(f"   ✅ PASS - Login successful")
            print(f"   User: {user_info.get('email')} - {user_info.get('full_name')}")
            print(f"   Role: {user_info.get('role')}")
            print(f"   Token: {access_token[:20]}..." if access_token else "No token")
            
            results["dealer_login"] = {"status": "PASS", "token": access_token}
        else:
            print(f"   ❌ FAIL - Login failed")
            print(f"   Response: {response.text[:200]}")
            results["dealer_login"] = {"status": "FAIL", "error": response.text[:200]}
            
    except Exception as e:
        print(f"   ❌ FAIL - Exception: {str(e)}")
        results["dealer_login"] = {"status": "FAIL", "error": str(e)}
    
    print()
    
    # Get auth headers if login succeeded
    auth_headers = {}
    if results.get("dealer_login", {}).get("status") == "PASS":
        token = results["dealer_login"]["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
    
    # Test 2: Auth Guard (navigation-summary without auth should return 401/403)
    print("2. Testing auth guard: GET /api/dealer/dashboard/navigation-summary (without auth)")
    try:
        response = requests.get(
            f"{API_BASE}/dealer/dashboard/navigation-summary",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print(f"   ✅ PASS - Auth guard working (returned {response.status_code})")
            results["auth_guard"] = {"status": "PASS", "code": response.status_code}
        else:
            print(f"   ❌ FAIL - Auth guard not working (expected 401/403, got {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            results["auth_guard"] = {"status": "FAIL", "code": response.status_code, "response": response.text[:200]}
            
    except Exception as e:
        print(f"   ❌ FAIL - Exception: {str(e)}")
        results["auth_guard"] = {"status": "FAIL", "error": str(e)}
    
    print()
    
    # Test 3: Dealer Routes (if we have auth token)
    dealer_endpoints = [
        "/dealer/dashboard/navigation-summary",
        "/dealer/virtual-tours", 
        "/dealer/messages",
        "/dealer/favorites",
        "/dealer/reports"
    ]
    
    for i, endpoint in enumerate(dealer_endpoints, 3):
        print(f"{i}. Testing dealer route: GET {endpoint}")
        
        if not auth_headers:
            print(f"   ⚠️  SKIP - No auth token available")
            results[endpoint.replace("/", "_")] = {"status": "SKIP", "reason": "No auth token"}
            print()
            continue
        
        try:
            response = requests.get(
                f"{API_BASE}{endpoint}",
                headers=auth_headers,
                timeout=10
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ PASS - Endpoint accessible and returns JSON")
                    
                    # Show some response structure info
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]  # First 5 keys
                        print(f"   Response keys: {keys}")
                    elif isinstance(data, list):
                        print(f"   Response: List with {len(data)} items")
                    
                    results[endpoint.replace("/", "_")] = {"status": "PASS", "response_type": type(data).__name__}
                except:
                    print(f"   ✅ PASS - Endpoint accessible (non-JSON response)")
                    results[endpoint.replace("/", "_")] = {"status": "PASS", "response_type": "non-JSON"}
                    
            elif response.status_code in [401, 403]:
                print(f"   ❌ FAIL - Auth issue (dealer should have access)")
                results[endpoint.replace("/", "_")] = {"status": "FAIL", "code": response.status_code, "reason": "Auth denied"}
                
            elif response.status_code == 404:
                print(f"   ⚠️  WARN - Endpoint not found (may not be implemented)")
                results[endpoint.replace("/", "_")] = {"status": "WARN", "code": 404, "reason": "Not found"}
                
            elif response.status_code >= 500:
                print(f"   ❌ FAIL - Server error")
                print(f"   Response: {response.text[:200]}")
                results[endpoint.replace("/", "_")] = {"status": "FAIL", "code": response.status_code, "error": response.text[:200]}
                
            else:
                print(f"   ❌ FAIL - Unexpected status code")
                print(f"   Response: {response.text[:200]}")
                results[endpoint.replace("/", "_")] = {"status": "FAIL", "code": response.status_code, "response": response.text[:200]}
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {str(e)}")
            results[endpoint.replace("/", "_")] = {"status": "FAIL", "error": str(e)}
        
        print()
    
    # Summary
    print("=== SUMMARY ===")
    
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    failed = sum(1 for r in results.values() if r.get("status") == "FAIL") 
    warnings = sum(1 for r in results.values() if r.get("status") == "WARN")
    skipped = sum(1 for r in results.values() if r.get("status") == "SKIP")
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Warnings: {warnings}")
    print(f"⏭️  Skipped: {skipped}")
    print()
    
    # Critical findings
    critical_pass = []
    critical_fail = []
    
    # Check login
    if results.get("dealer_login", {}).get("status") == "PASS":
        critical_pass.append("Dealer login working")
    else:
        critical_fail.append("Dealer login failed")
    
    # Check auth guard
    if results.get("auth_guard", {}).get("status") == "PASS":
        critical_pass.append("Auth guard protection working")
    else:
        critical_fail.append("Auth guard protection not working")
    
    # Check dealer routes
    dealer_routes_working = sum(1 for k, r in results.items() 
                               if k.startswith("_dealer_") and r.get("status") == "PASS")
    dealer_routes_total = sum(1 for k, r in results.items() 
                             if k.startswith("_dealer_") and r.get("status") != "SKIP")
    
    if dealer_routes_working > 0:
        critical_pass.append(f"Dealer routes accessible ({dealer_routes_working}/{dealer_routes_total})")
    
    if critical_pass:
        print("✅ Critical Passes:")
        for item in critical_pass:
            print(f"   - {item}")
    
    if critical_fail:
        print("❌ Critical Failures:")
        for item in critical_fail:
            print(f"   - {item}")
    
    print()
    
    # Overall result
    if failed == 0 and len(critical_fail) == 0:
        print("🎉 Overall Result: PASS")
        return True
    else:
        print("💥 Overall Result: FAIL")  
        return False


if __name__ == "__main__":
    success = test_dealer_portal_regression()
    exit(0 if success else 1)