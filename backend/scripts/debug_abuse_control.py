
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

async def debug_abuse_control():
    print("🚀 Debugging Abuse Control...")
    
    device_hash = "unique_device_debug"
    
    # Clean previous run
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM users WHERE email LIKE 'debug_%@test.com'"))
        await session.commit()
    
    base_url = "http://localhost:8001/api"
    
    async with httpx.AsyncClient() as client:
        for i in range(4):
            email = f"debug_{i}_{uuid.uuid4().hex[:4]}@test.com"
            payload = {
                "email": email,
                "password": "password",
                "full_name": f"Debug {i}",
                "device_hash": device_hash
            }
            resp = await client.post(f"{base_url}/auth/register", json=payload)
            print(f"Attempt {i+1}: {resp.status_code}")
            
    print("🎉 Debug Finished")

if __name__ == "__main__":
    asyncio.run(debug_abuse_control())
