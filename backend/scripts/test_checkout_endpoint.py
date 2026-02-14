
import asyncio
import httpx
import os
import json

API_URL = "http://localhost:8001/api/v1/billing/checkout"

async def test_checkout():
    print("🚀 Testing Checkout API...")
    
    # 1. Login (Mock) or User Injection
    # We need a token. Or we can mock the dependency in a test script. 
    # For quick check, I'll assume I can't easily get a token without login flow.
    # But I can check if endpoint exists and returns 401.
    
    async with httpx.AsyncClient() as client:
        res = await client.post(API_URL, json={"plan_code": "TR_DEALER_PRO"})
        print(f"Status: {res.status_code}")
        if res.status_code == 401:
            print("✅ 401 Unauthorized (Expected without token)")
        elif res.status_code == 200:
            print(f"✅ Success: {res.json()}")
        else:
            print(f"❌ Error: {res.text}")

if __name__ == "__main__":
    asyncio.run(test_checkout())
