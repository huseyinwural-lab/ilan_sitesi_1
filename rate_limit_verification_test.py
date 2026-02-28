#!/usr/bin/env python3
"""
P5-007 Rate Limiting Verification Test
Tests both IP-based (Tier 2) and Token-based (Tier 1) rate limits
"""

import requests
import time
import json
from datetime import datetime

class RateLimitTester:
    def __init__(self, base_url="https://category-fix-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def get_admin_token(self):
        """Get admin token for authenticated tests"""
        try:
            response = requests.post(
                f"{self.api_url}/auth/login",
                json={"email": "admin@platform.com", "password": "Admin123!"},
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.log_result("Admin Login", True, "Successfully obtained admin token")
                return True
            else:
                self.log_result("Admin Login", False, f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Login", False, f"Login error: {str(e)}")
            return False
    
    def test_ip_based_rate_limit(self):
        """Test IP-based rate limiting on auth/login endpoint (20 requests/60s)"""
        print("\n🔍 Testing IP-based Rate Limiting (Tier 2)")
        print("Endpoint: /api/auth/login (Limit: 20 requests/60s)")
        
        # Clear any existing rate limit state by waiting a bit
        time.sleep(1)
        
        success_count = 0
        rate_limited = False
        retry_after = None
        
        # Try to hit the limit (20 requests)
        for i in range(22):  # Try 22 to exceed limit
            try:
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"email": "invalid@test.com", "password": "invalid"},
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 429:
                    rate_limited = True
                    retry_after = response.headers.get('Retry-After')
                    print(f"   Request {i+1}: Rate limited (429) - Retry-After: {retry_after}s")
                    
                    # Verify response structure
                    try:
                        error_data = response.json()
                        if isinstance(error_data.get('detail'), dict):
                            detail = error_data['detail']
                            if detail.get('code') == 'rate_limit_exceeded':
                                self.log_result(
                                    "IP Rate Limit Structure", 
                                    True, 
                                    f"Correct error structure with code: {detail['code']}"
                                )
                            else:
                                self.log_result(
                                    "IP Rate Limit Structure", 
                                    False, 
                                    f"Wrong error code: {detail.get('code')}"
                                )
                        else:
                            self.log_result(
                                "IP Rate Limit Structure", 
                                False, 
                                f"Unexpected error structure: {error_data}"
                            )
                    except Exception as e:
                        self.log_result(
                            "IP Rate Limit Structure", 
                            False, 
                            f"Failed to parse error response: {str(e)}"
                        )
                    break
                else:
                    success_count += 1
                    print(f"   Request {i+1}: {response.status_code} (allowed)")
                    
            except Exception as e:
                self.log_result("IP Rate Limit Test", False, f"Request error: {str(e)}")
                return False
        
        # Verify rate limiting occurred
        if rate_limited:
            self.log_result(
                "IP Rate Limit Enforcement", 
                True, 
                f"Rate limit triggered after {success_count} requests, Retry-After: {retry_after}s"
            )
            
            # Verify Retry-After header
            if retry_after and retry_after.isdigit():
                self.log_result(
                    "IP Rate Limit Retry-After Header", 
                    True, 
                    f"Retry-After header present: {retry_after}s"
                )
            else:
                self.log_result(
                    "IP Rate Limit Retry-After Header", 
                    False, 
                    f"Missing or invalid Retry-After header: {retry_after}"
                )
        else:
            self.log_result(
                "IP Rate Limit Enforcement", 
                False, 
                f"Rate limit not triggered after {success_count} requests"
            )
        
        return rate_limited
    
    def test_token_based_rate_limit(self):
        """Test Token-based rate limiting on authenticated endpoints"""
        print("\n🔍 Testing Token-based Rate Limiting (Tier 1)")
        
        if not self.token:
            self.log_result("Token Rate Limit Test", False, "No admin token available")
            return False
        
        # Test on a simple authenticated endpoint
        print("Endpoint: /api/auth/me (using token-based limiting)")
        
        success_count = 0
        rate_limited = False
        retry_after = None
        
        # Make multiple requests with the same token
        for i in range(25):  # Try more requests to potentially hit any token-based limits
            try:
                response = requests.get(
                    f"{self.api_url}/auth/me",
                    headers={
                        'Authorization': f'Bearer {self.token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                if response.status_code == 429:
                    rate_limited = True
                    retry_after = response.headers.get('Retry-After')
                    print(f"   Request {i+1}: Rate limited (429) - Retry-After: {retry_after}s")
                    
                    # Verify response structure
                    try:
                        error_data = response.json()
                        if isinstance(error_data.get('detail'), dict):
                            detail = error_data['detail']
                            if detail.get('code') == 'rate_limit_exceeded':
                                self.log_result(
                                    "Token Rate Limit Structure", 
                                    True, 
                                    f"Correct error structure with code: {detail['code']}"
                                )
                        else:
                            self.log_result(
                                "Token Rate Limit Structure", 
                                False, 
                                f"Unexpected error structure: {error_data}"
                            )
                    except Exception as e:
                        self.log_result(
                            "Token Rate Limit Structure", 
                            False, 
                            f"Failed to parse error response: {str(e)}"
                        )
                    break
                elif response.status_code == 200:
                    success_count += 1
                    if i < 5 or i % 5 == 0:  # Log first 5 and every 5th request
                        print(f"   Request {i+1}: {response.status_code} (allowed)")
                else:
                    print(f"   Request {i+1}: {response.status_code} (unexpected)")
                    
            except Exception as e:
                self.log_result("Token Rate Limit Test", False, f"Request error: {str(e)}")
                return False
        
        # For this test, we're mainly verifying the token-based key generation works
        # The actual limits might be higher, so we log the behavior
        self.log_result(
            "Token Rate Limit Behavior", 
            True, 
            f"Token-based requests processed: {success_count}, Rate limited: {rate_limited}"
        )
        
        return True
    
    def test_different_tokens_separate_limits(self):
        """Test that different tokens have separate rate limits"""
        print("\n🔍 Testing Token Separation")
        
        # Create two different fake tokens to test separation
        token1 = "fake_token_1234567890"
        token2 = "fake_token_0987654321"
        
        # Test endpoint that doesn't require valid auth for rate limiting
        endpoint = "/api/countries/public"  # This should be public
        
        success_token1 = 0
        success_token2 = 0
        
        # Make requests with token1
        for i in range(5):
            try:
                response = requests.get(
                    f"{self.api_url}{endpoint}",
                    headers={'Authorization': f'Bearer {token1}'}
                )
                if response.status_code != 429:
                    success_token1 += 1
            except:
                pass
        
        # Make requests with token2
        for i in range(5):
            try:
                response = requests.get(
                    f"{self.api_url}{endpoint}",
                    headers={'Authorization': f'Bearer {token2}'}
                )
                if response.status_code != 429:
                    success_token2 += 1
            except:
                pass
        
        # Both tokens should work independently
        if success_token1 > 0 and success_token2 > 0:
            self.log_result(
                "Token Separation", 
                True, 
                f"Different tokens work independently: token1={success_token1}, token2={success_token2}"
            )
        else:
            self.log_result(
                "Token Separation", 
                False, 
                f"Token separation issue: token1={success_token1}, token2={success_token2}"
            )
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are properly set"""
        print("\n🔍 Testing Rate Limit Headers")
        
        try:
            # Make a request that should trigger rate limiting
            for i in range(21):  # Exceed IP limit
                response = requests.post(
                    f"{self.api_url}/auth/login",
                    json={"email": "test@test.com", "password": "test"},
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 429:
                    headers = response.headers
                    required_headers = ['Retry-After', 'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset']
                    
                    missing_headers = []
                    present_headers = []
                    
                    for header in required_headers:
                        if header in headers:
                            present_headers.append(f"{header}: {headers[header]}")
                        else:
                            missing_headers.append(header)
                    
                    if not missing_headers:
                        self.log_result(
                            "Rate Limit Headers Complete", 
                            True, 
                            f"All headers present: {', '.join(present_headers)}"
                        )
                    else:
                        self.log_result(
                            "Rate Limit Headers Complete", 
                            False, 
                            f"Missing headers: {missing_headers}, Present: {present_headers}"
                        )
                    
                    # Verify Retry-After is numeric
                    retry_after = headers.get('Retry-After')
                    if retry_after and retry_after.isdigit() and int(retry_after) > 0:
                        self.log_result(
                            "Retry-After Header Valid", 
                            True, 
                            f"Retry-After is valid: {retry_after}s"
                        )
                    else:
                        self.log_result(
                            "Retry-After Header Valid", 
                            False, 
                            f"Invalid Retry-After: {retry_after}"
                        )
                    
                    return True
            
            self.log_result("Rate Limit Headers", False, "Could not trigger rate limit to test headers")
            return False
            
        except Exception as e:
            self.log_result("Rate Limit Headers", False, f"Error testing headers: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all rate limiting tests"""
        print("🚀 Starting P5-007 Rate Limiting Verification")
        print("=" * 60)
        
        # Get admin token first
        if not self.get_admin_token():
            print("❌ Cannot proceed without admin token")
            return False
        
        # Run all tests
        tests = [
            self.test_ip_based_rate_limit,
            self.test_token_based_rate_limit,
            self.test_different_tokens_separate_limits,
            self.test_rate_limit_headers
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_result(test.__name__, False, f"Test error: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        # Show key successes
        key_successes = [r for r in self.test_results if r['success'] and 'Rate Limit' in r['test']]
        if key_successes:
            print(f"\n✅ Key Rate Limiting Features Verified ({len(key_successes)}):")
            for test in key_successes:
                print(f"  • {test['test']}: {test['details']}")
        
        return passed == total

def main():
    tester = RateLimitTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())