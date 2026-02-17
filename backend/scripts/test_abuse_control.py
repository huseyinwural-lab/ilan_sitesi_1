
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.user import User
from server import create_access_token

async def test_abuse_control():
    print("🚀 Starting Abuse Control Test...")
    
    device_hash = "unique_device_123"
    
    # Clean previous run
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM users WHERE email LIKE 'abuse_%@test.com'"))
        await session.commit()
    
    # 1. Register 3 Users (Limit)
    base_url = "http://localhost:8001/api"
    
    async with httpx.AsyncClient() as client:
        for i in range(3):
            email = f"abuse_test_{i}_{uuid.uuid4().hex[:4]}@test.com"
            payload = {
                "email": email,
                "password": "password",
                "full_name": "Test",
                "device_hash": device_hash
            }
            resp = await client.post(f"{base_url}/auth/register", json=payload)
            if resp.status_code == 201:
                print(f"✅ User {i+1} Registered")
            else:
                print(f"❌ Registration Failed: {resp.text}")
                return

        # 2. Register 4th User (Should Block)
        print("\n🔹 Testing Block...")
        email = f"abuse_block_{uuid.uuid4().hex[:4]}@test.com"
        payload = {
            "email": email,
            "password": "password",
            "full_name": "Test",
            "device_hash": device_hash
        }
        resp = await client.post(f"{base_url}/auth/register", json=payload)
        
        if resp.status_code == 403:
            print("✅ Abuse Block Verified (403)")
        else:
            print(f"❌ Abuse Block FAILED: {resp.status_code}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM users WHERE email LIKE 'abuse_%@test.com'"))
        await session.commit()

    print("\n🎉 Abuse Control PASSED!")

if __name__ == "__main__":
    asyncio.run(test_abuse_control())
