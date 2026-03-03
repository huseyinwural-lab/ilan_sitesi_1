#!/usr/bin/env python3

import requests
import json
import sys

# Configuration
BASE_URL = "https://header-config-1.preview.emergentagent.com/api"
DEALER_CREDENTIALS = {
    "email": "dealer@platform.com",
    "password": "Dealer123!"
}

class DealerBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_results = []

    def log_test(self, test_name, success, status_code, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "status_code": status_code,
            "details": details
        }
        self.test_results.append(result)
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}: {status_code} - {details}")

    def test_dealer_login(self):
        """Test POST /api/auth/login with dealer credentials"""
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=DEALER_CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                if self.access_token:
                    # Set auth header for subsequent requests
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}"
                    })
                    user_email = data.get("user", {}).get("email", "Unknown")
                    self.log_test(
                        "POST /api/auth/login (dealer)",
                        True,
                        200,
                        f"Login successful, token received, user: {user_email}"
                    )
                    return True
                else:
                    self.log_test(
                        "POST /api/auth/login (dealer)",
                        False,
                        200,
                        "Response 200 but no access token in response"
                    )
                    return False
            else:
                self.log_test(
                    "POST /api/auth/login (dealer)",
                    False,
                    response.status_code,
                    f"Login failed: {response.text}"
                )
                return False
                
        except requests.RequestException as e:
            self.log_test(
                "POST /api/auth/login (dealer)",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_portal_config(self):
        """Test GET /api/dealer/portal/config"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/portal/config",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Portal config retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/portal/config",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/portal/config",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_navigation_summary(self):
        """Test GET /api/dealer/dashboard/navigation-summary"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/dashboard/navigation-summary",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Navigation summary retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/dashboard/navigation-summary",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/dashboard/navigation-summary",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_messages_inbox(self):
        """Test GET /api/dealer/messages?folder=inbox"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/messages",
                params={"folder": "inbox"},
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Messages inbox retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/messages?folder=inbox",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/messages?folder=inbox",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def test_dealer_settings_preferences(self):
        """Test GET /api/dealer/settings/preferences"""
        try:
            response = self.session.get(
                f"{BASE_URL}/dealer/settings/preferences",
                timeout=10
            )
            
            success = response.status_code == 200
            details = "Settings preferences retrieved successfully" if success else f"Error: {response.text}"
            
            self.log_test(
                "GET /api/dealer/settings/preferences",
                success,
                response.status_code,
                details
            )
            return success
            
        except requests.RequestException as e:
            self.log_test(
                "GET /api/dealer/settings/preferences",
                False,
                "ERROR",
                f"Request exception: {str(e)}"
            )
            return False

    def run_all_tests(self):
        """Run all dealer backend regression tests"""
        print("🚀 Starting Dealer Portal Backend Regression Tests...")
        print("=" * 60)
        
        # Step 1: Authenticate
        login_success = self.test_dealer_login()
        if not login_success:
            print("\n❌ CRITICAL: Dealer login failed. Stopping tests.")
            return False
            
        print("\n🔐 Authentication successful. Running API tests...")
        print("-" * 60)
        
        # Step 2: Test all dealer endpoints
        tests = [
            self.test_dealer_portal_config,
            self.test_dealer_navigation_summary,
            self.test_dealer_messages_inbox,
            self.test_dealer_settings_preferences
        ]
        
        all_passed = True
        for test_func in tests:
            success = test_func()
            if not success:
                all_passed = False
                
        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 DEALER PORTAL BACKEND REGRESSION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        
        for result in self.test_results:
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {result['test']}: {result['status_code']}")
            
        print(f"\n📈 Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
        
        if passed == total:
            print("🎉 OVERALL RESULT: PASS - All dealer portal endpoints working correctly")
            return True
        else:
            print("⚠️ OVERALL RESULT: FAIL - Some dealer portal endpoints have issues")
            return False

def main():
    """Main test execution function"""
    tester = DealerBackendTester()
    
    try:
        # Run all tests
        overall_success = tester.run_all_tests()
        
        # Print summary
        final_result = tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if final_result else 1)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()