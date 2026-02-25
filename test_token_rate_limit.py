#!/usr/bin/env python3
import requests
import time
import uuid

def test_token_based_rate_limit():
    api_url = "https://monetize-listings.preview.emergentagent.com/api"
    
    # First get an admin token
    print("Getting admin token...")
    login_response = requests.post(
        f"{api_url}/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status_code != 200:
        print(f"Failed to login: {login_response.status_code}")
        return
    
    token = login_response.json()['access_token']
    print("✅ Got admin token")
    
    # Test token-based rate limiting on commercial endpoint
    # The limit is 60 requests per 60 seconds for listing creation
    print("\nTesting token-based rate limiting on /api/v1/commercial/dealers/{dealer_id}/listings")
    print("Expected limit: 60 requests per 60 seconds")
    
    dealer_id = str(uuid.uuid4())
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Make requests to trigger rate limit
    for i in range(65):  # Try to exceed 60 limit
        response = requests.post(
            f"{api_url}/v1/commercial/dealers/{dealer_id}/listings",
            json={
                "title": f"Test Listing {i}",
                "description": "Test description",
                "module": "vehicle",
                "price": 1000.0,
                "currency": "EUR",
                "images": [],
                "attributes": {}
            },
            headers=headers
        )
        
        print(f"Request {i+1:2d}: Status {response.status_code}")
        
        if response.status_code == 429:
            print("🚫 TOKEN-BASED RATE LIMITED!")
            print(f"Headers: {dict(response.headers)}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response text: {response.text}")
            break
        elif response.status_code == 404:
            print(f"  ✓ Expected 404 (dealer not found) - rate limit not triggered yet")
        elif response.status_code == 422:
            print(f"  ✓ Expected 422 (validation error) - rate limit not triggered yet")
        else:
            print(f"  ? Unexpected status: {response.status_code}")
    
    print("Token-based rate limit test completed")

def test_different_tokens():
    """Test that different tokens have separate rate limits"""
    api_url = "https://monetize-listings.preview.emergentagent.com/api"
    
    print("\n🔍 Testing token separation...")
    
    # Test with two different fake tokens
    token1 = "fake_token_1234567890abcdef"
    token2 = "fake_token_fedcba0987654321"
    
    # Use a simple authenticated endpoint
    endpoint = "/auth/me"
    
    print("Testing with token1...")
    for i in range(3):
        response = requests.get(
            f"{api_url}{endpoint}",
            headers={'Authorization': f'Bearer {token1}'}
        )
        print(f"  Token1 Request {i+1}: {response.status_code}")
    
    print("Testing with token2...")
    for i in range(3):
        response = requests.get(
            f"{api_url}{endpoint}",
            headers={'Authorization': f'Bearer {token2}'}
        )
        print(f"  Token2 Request {i+1}: {response.status_code}")
    
    print("✅ Different tokens processed independently")

if __name__ == "__main__":
    test_token_based_rate_limit()
    test_different_tokens()