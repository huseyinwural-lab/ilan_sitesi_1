#!/usr/bin/env python3
"""
Backend API Testing for P1-Next-01 and P1-Next-02
Testing user/dealer permission validation and RBAC backend enforcement.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, List

# Get backend URL from frontend .env file
BACKEND_URL = "https://marketplace-admin-13.preview.emergentagent.com/api"

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com" 
USER_PASSWORD = "User123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"

class BackendTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.dealer_token = None
        
    def login(self, email: str, password: str, portal_type: str = "individual") -> Dict[str, Any]:
        """Login and get access token"""
        url = f"{BACKEND_URL}/auth/login"
        payload = {
            "email": email,
            "password": password,
            "portal_type": portal_type
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            print(f"Login {email} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return {"success": True, "token": data.get("access_token"), "data": data}
            else:
                return {"success": False, "error": f"Status {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def make_authenticated_request(self, token: str, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = f"{BACKEND_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, json=data, headers=headers, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
                
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.text[:500] if response.text else "",
                "response": response
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def setup_tokens(self):
        """Login all users and get tokens"""
        print("=== SETTING UP AUTHENTICATION TOKENS ===")
        
        # Admin login
        admin_result = self.login(ADMIN_EMAIL, ADMIN_PASSWORD, "individual")
        if admin_result["success"]:
            self.admin_token = admin_result["token"]
            print(f"✅ Admin login successful")
        else:
            print(f"❌ Admin login failed: {admin_result['error']}")
        
        # User login
        user_result = self.login(USER_EMAIL, USER_PASSWORD, "individual")
        if user_result["success"]:
            self.user_token = user_result["token"]
            print(f"✅ User login successful")
        else:
            print(f"❌ User login failed: {user_result['error']}")
            
        # Dealer login
        dealer_result = self.login(DEALER_EMAIL, DEALER_PASSWORD, "dealer")
        if dealer_result["success"]:
            self.dealer_token = dealer_result["token"]
            print(f"✅ Dealer login successful")
        else:
            print(f"❌ Dealer login failed: {dealer_result['error']}")
        
        print()
        
    def test_p1_next_01_permission_validation(self):
        """Test P1-Next-01: user/dealer permission validation endpoints"""
        print("=== P1-Next-01: USER/DEALER PERMISSION VALIDATION ===")
        
        results = {
            "user_account_endpoints": {},
            "dealer_account_endpoints": {},
            "negative_admin_access": {}
        }
        
        # 1. Test user account endpoints
        print("\n1. Testing user account endpoints:")
        user_endpoints = [
            "/account/invoices",
            "/account/payments", 
            "/account/subscription"
        ]
        
        for endpoint in user_endpoints:
            print(f"  Testing {endpoint}")
            result = self.make_authenticated_request(self.user_token, endpoint)
            results["user_account_endpoints"][endpoint] = result
            if result["success"]:
                expected_codes = [200, 404]  # 404 acceptable for empty data
                if result["status_code"] in expected_codes:
                    print(f"    ✅ User access OK - Status: {result['status_code']}")
                else:
                    print(f"    ⚠️  User access - Status: {result['status_code']}")
            else:
                print(f"    ❌ User access failed: {result['error']}")
        
        # 2. Test dealer invoices endpoint  
        print("\n2. Testing dealer invoices endpoint:")
        dealer_endpoint = "/dealer/invoices"
        result = self.make_authenticated_request(self.dealer_token, dealer_endpoint)
        results["dealer_account_endpoints"][dealer_endpoint] = result
        if result["success"]:
            expected_codes = [200, 404]  # 404 acceptable for empty data
            if result["status_code"] in expected_codes:
                print(f"    ✅ Dealer access OK - Status: {result['status_code']}")
            else:
                print(f"    ⚠️  Dealer access - Status: {result['status_code']}")
        else:
            print(f"    ❌ Dealer access failed: {result['error']}")
            
        # 3. Test negative permissions (user/dealer trying admin endpoints)
        print("\n3. Testing negative permissions (user/dealer -> admin endpoints):")
        admin_endpoints = [
            "/admin/finance/overview",
            "/admin/finance/subscriptions", 
            "/admin/finance/ledger",
            "/admin/invoices/export/csv",
            "/admin/payments/export/csv"
        ]
        
        for endpoint in admin_endpoints:
            print(f"  Testing {endpoint}")
            
            # Test user trying admin endpoint
            user_result = self.make_authenticated_request(self.user_token, endpoint)
            results["negative_admin_access"][f"user->{endpoint}"] = user_result
            if user_result["success"] and user_result["status_code"] == 403:
                print(f"    ✅ User properly blocked (403) from {endpoint}")
            elif user_result["success"]:
                print(f"    ❌ User NOT blocked from {endpoint} - Status: {user_result['status_code']}")
            else:
                print(f"    ⚠️  User test error for {endpoint}: {user_result['error']}")
                
            # Test dealer trying admin endpoint
            dealer_result = self.make_authenticated_request(self.dealer_token, endpoint)
            results["negative_admin_access"][f"dealer->{endpoint}"] = dealer_result
            if dealer_result["success"] and dealer_result["status_code"] == 403:
                print(f"    ✅ Dealer properly blocked (403) from {endpoint}")
            elif dealer_result["success"]:
                print(f"    ❌ Dealer NOT blocked from {endpoint} - Status: {dealer_result['status_code']}")
            else:
                print(f"    ⚠️  Dealer test error for {endpoint}: {dealer_result['error']}")
        
        return results
        
    def test_p1_next_02_rbac_enforcement(self):
        """Test P1-Next-02: RBAC backend enforcement"""
        print("\n=== P1-Next-02: RBAC BACKEND ENFORCEMENT ===")
        
        results = {
            "super_admin_access": {},
            "non_admin_blocking": {}
        }
        
        # Test endpoints
        rbac_endpoints = [
            "/admin/audit/dashboard/stats",
            "/admin/permissions/snapshot"
        ]
        
        print("\n1. Testing super_admin access:")
        for endpoint in rbac_endpoints:
            print(f"  Testing {endpoint}")
            result = self.make_authenticated_request(self.admin_token, endpoint)
            results["super_admin_access"][endpoint] = result
            if result["success"] and result["status_code"] == 200:
                print(f"    ✅ Super admin access OK - Status: {result['status_code']}")
            elif result["success"]:
                print(f"    ⚠️  Super admin access - Status: {result['status_code']} (might need specific permissions)")
            else:
                print(f"    ❌ Super admin access failed: {result['error']}")
                
        print("\n2. Testing non-admin blocking:")
        for endpoint in rbac_endpoints:
            print(f"  Testing {endpoint}")
            
            # Test user trying admin endpoint
            user_result = self.make_authenticated_request(self.user_token, endpoint)
            results["non_admin_blocking"][f"user->{endpoint}"] = user_result
            if user_result["success"] and user_result["status_code"] == 403:
                print(f"    ✅ User properly blocked (403) from {endpoint}")
            elif user_result["success"]:
                print(f"    ❌ User NOT blocked from {endpoint} - Status: {user_result['status_code']}")
            else:
                print(f"    ⚠️  User test error for {endpoint}: {user_result['error']}")
                
            # Test dealer trying admin endpoint  
            dealer_result = self.make_authenticated_request(self.dealer_token, endpoint)
            results["non_admin_blocking"][f"dealer->{endpoint}"] = dealer_result
            if dealer_result["success"] and dealer_result["status_code"] == 403:
                print(f"    ✅ Dealer properly blocked (403) from {endpoint}")
            elif dealer_result["success"]:
                print(f"    ❌ Dealer NOT blocked from {endpoint} - Status: {dealer_result['status_code']}")
            else:
                print(f"    ⚠️  Dealer test error for {endpoint}: {dealer_result['error']}")
        
        return results
        
    def run_full_test(self):
        """Run complete backend permission validation test"""
        print("Backend API Testing for P1-Next-01 and P1-Next-02")
        print("=" * 60)
        
        # Setup authentication
        self.setup_tokens()
        
        if not all([self.admin_token, self.user_token, self.dealer_token]):
            print("❌ Failed to obtain all required tokens. Cannot continue.")
            return False
            
        # Run tests
        p1_01_results = self.test_p1_next_01_permission_validation()
        p1_02_results = self.test_p1_next_02_rbac_enforcement()
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        # P1-Next-01 Summary
        print("\nP1-Next-01 User/Dealer Permission Validation:")
        
        # Count user endpoint successes
        user_success = 0
        user_total = 0
        for endpoint, result in p1_01_results["user_account_endpoints"].items():
            user_total += 1
            if result["success"] and result["status_code"] in [200, 404]:
                user_success += 1
        print(f"  User account endpoints: {user_success}/{user_total} working")
        
        # Count dealer endpoint successes
        dealer_success = 0
        dealer_total = 0
        for endpoint, result in p1_01_results["dealer_account_endpoints"].items():
            dealer_total += 1
            if result["success"] and result["status_code"] in [200, 404]:
                dealer_success += 1
        print(f"  Dealer invoices endpoint: {dealer_success}/{dealer_total} working")
        
        # Count negative permission blocks
        negative_success = 0
        negative_total = 0
        for test_name, result in p1_01_results["negative_admin_access"].items():
            negative_total += 1
            if result["success"] and result["status_code"] == 403:
                negative_success += 1
        print(f"  Negative permissions (403 blocks): {negative_success}/{negative_total} correct")
        
        # P1-Next-02 Summary
        print("\nP1-Next-02 RBAC Backend Enforcement:")
        
        # Count super admin successes
        admin_success = 0
        admin_total = 0
        for endpoint, result in p1_02_results["super_admin_access"].items():
            admin_total += 1
            if result["success"] and result["status_code"] == 200:
                admin_success += 1
        print(f"  Super admin access: {admin_success}/{admin_total} working")
        
        # Count non-admin blocks
        rbac_success = 0
        rbac_total = 0
        for test_name, result in p1_02_results["non_admin_blocking"].items():
            rbac_total += 1
            if result["success"] and result["status_code"] == 403:
                rbac_success += 1
        print(f"  Non-admin blocking (403): {rbac_success}/{rbac_total} correct")
        
        # Overall assessment
        total_tests = user_total + dealer_total + negative_total + admin_total + rbac_total
        total_passed = user_success + dealer_success + negative_success + admin_success + rbac_success
        
        print(f"\nOverall: {total_passed}/{total_tests} tests passed")
        
        # Determine final result
        critical_issues = []
        
        if user_success < user_total:
            critical_issues.append("User account endpoints not fully working")
        if dealer_success < dealer_total:
            critical_issues.append("Dealer invoices endpoint not working")
        if negative_success < negative_total:
            critical_issues.append("Admin endpoints not properly blocked for users/dealers")
        if admin_success < admin_total:
            critical_issues.append("Super admin endpoints not accessible")
        if rbac_success < rbac_total:
            critical_issues.append("RBAC enforcement not working properly")
            
        if critical_issues:
            print(f"\n❌ CRITICAL ISSUES FOUND:")
            for issue in critical_issues:
                print(f"  - {issue}")
            return False
        else:
            print(f"\n✅ ALL TESTS PASSED - Backend permission validation working correctly")
            return True

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_full_test()
    sys.exit(0 if success else 1)