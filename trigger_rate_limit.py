#!/usr/bin/env python3
import requests
import time

def trigger_rate_limit():
    api_url = "https://category-wizard-1.preview.emergentagent.com/api"
    
    print("Attempting to trigger rate limit (20 requests/60s)...")
    for i in range(25):
        response = requests.post(
            f"{api_url}/auth/login",
            json={"email": "test@example.com", "password": "test"},
            headers={'Content-Type': 'application/json'}
        )
        print(f"Request {i+1:2d}: Status {response.status_code}")
        
        if response.status_code == 429:
            print("🚫 RATE LIMITED!")
            print(f"Headers: {dict(response.headers)}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response text: {response.text}")
            break
        
        # No delay - rapid fire to trigger limit
    
    print("Test completed")

if __name__ == "__main__":
    trigger_rate_limit()