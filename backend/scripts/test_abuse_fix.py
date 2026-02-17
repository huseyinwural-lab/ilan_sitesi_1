
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

async def test_abuse_fix():
    print("🚀 Starting Abuse Control Test (Fix Verification)...")
    
    device_hash = "unique_device_fix"
    
    # Clean previous run
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM users WHERE email LIKE 'abuse_fix_%@test.com'"))
        await session.commit()
    
    base_url = "http://localhost:8001/api"
    
    async with httpx.AsyncClient() as client:
        # Register 1
        print("🔹 Registering User 1...")
        resp = await client.post(f"{base_url}/auth/register", json={"email": f"abuse_fix_1@test.com", "password": "password123", "full_name": "Test User", "device_hash": device_hash})
        print(f"Status: {resp.status_code}") # Expect 201
        
        # Register 2
        print("🔹 Registering User 2...")
        resp = await client.post(f"{base_url}/auth/register", json={"email": f"abuse_fix_2@test.com", "password": "password123", "full_name": "Test User", "device_hash": device_hash})
        print(f"Status: {resp.status_code}") # Expect 201
        
        # Register 3
        print("🔹 Registering User 3...")
        resp = await client.post(f"{base_url}/auth/register", json={"email": f"abuse_fix_3@test.com", "password": "password123", "full_name": "Test User", "device_hash": device_hash})
        print(f"Status: {resp.status_code}") # Expect 201
        
        # Register 4 (BLOCK)
        print("🔹 Registering User 4 (Should Block)...")
        resp = await client.post(f"{base_url}/auth/register", json={"email": f"abuse_fix_4@test.com", "password": "password123", "full_name": "Test User", "device_hash": device_hash})
        print(f"Status: {resp.status_code}") # Expect 403
        
        if resp.status_code == 403:
            print("✅ Abuse Block Verified")
        else:
            print(f"❌ Abuse Block FAILED: {resp.status_code}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM users WHERE email LIKE 'abuse_fix_%@test.com'"))
        await session.commit()

if __name__ == "__main__":
    asyncio.run(test_abuse_fix())
