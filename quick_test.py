#!/usr/bin/env python3
import requests
import time

def quick_test():
    api_url = "https://config-telemetry.preview.emergentagent.com/api"
    
    print("Making 3 quick requests to see rate limiter logs...")
    for i in range(3):
        response = requests.post(
            f"{api_url}/auth/login",
            json={"email": "test@example.com", "password": "test"},
            headers={'Content-Type': 'application/json'}
        )
        print(f"Request {i+1}: {response.status_code}")
        time.sleep(0.5)

if __name__ == "__main__":
    quick_test()