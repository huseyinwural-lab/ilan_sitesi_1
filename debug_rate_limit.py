#!/usr/bin/env python3
"""
Debug Rate Limiting Test - Check if rate limiter is working
"""

import requests
import time
import json

def test_rate_limit_debug():
    base_url = "https://feature-complete-36.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🔍 Debug Rate Limiting Test")
    print("Testing /api/auth/login endpoint")
    print("Expected limit: 20 requests per 60 seconds")
    print("-" * 50)
    
    # Make requests rapidly
    for i in range(25):
        try:
            start_time = time.time()
            response = requests.post(
                f"{api_url}/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            end_time = time.time()
            
            print(f"Request {i+1:2d}: Status {response.status_code}, Time: {end_time-start_time:.2f}s")
            
            if response.status_code == 429:
                print(f"  🚫 RATE LIMITED!")
                print(f"  Headers: {dict(response.headers)}")
                try:
                    error_data = response.json()
                    print(f"  Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"  Response text: {response.text}")
                break
            elif response.status_code == 401:
                print(f"  ✓ Expected auth failure")
            else:
                print(f"  ? Unexpected status: {response.status_code}")
                
            # Small delay to avoid overwhelming
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Request {i+1}: ERROR - {str(e)}")
            break
    
    print("\n" + "=" * 50)
    print("Debug test completed")

if __name__ == "__main__":
    test_rate_limit_debug()