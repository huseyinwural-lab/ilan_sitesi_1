import asyncio
import sys
import os
import httpx
from sqlalchemy import select

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token

async def test_access_control():
    print("🛡️ Starting Access Control Penetration Test...")
    
    # 1. Create Malicious User (Standard Role)
    user_id = "11111111-1111-1111-1111-111111111111" # Mock ID
    token_data = {"sub": user_id, "email": "hacker@test.com", "role": "user"} # Role 'user' is NOT 'super_admin'
    token = create_access_token(token_data)
    
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8001/api"
    
    async with httpx.AsyncClient() as client:
        # Test 1: Try to Create Feature Flag (Admin Only)
        print("🔹 Test 1: Attempting Admin Action (Create Feature Flag)...")
        resp = await client.post(
            f"{base_url}/feature-flags", 
            json={"key": "hacked_flag", "name": {"en": "Hacked"}, "scope": "global"},
            headers=headers
        )
        
        if resp.status_code == 403:
            print("✅ PASS: Admin Endpoint Protected (403 Forbidden)")
        else:
            print(f"❌ FAIL: Admin Endpoint Exposed! Status: {resp.status_code}")
            sys.exit(1)

        # Test 2: Try to Delete User (Admin Only)
        print("🔹 Test 2: Attempting Destructive Action (Delete User)...")
        # Trying to delete self or random ID
        resp = await client.delete(
            f"{base_url}/users/{user_id}",
            headers=headers
        )
        
        if resp.status_code == 403 or resp.status_code == 401:
             print("✅ PASS: Delete Endpoint Protected (403/401)")
        else:
             # Note: logic might allow deleting self, but usually admin delete is protected.
             # In our server.py: delete_user checks check_permissions(["super_admin"])
             print(f"❌ FAIL: Delete Endpoint Exposed! Status: {resp.status_code}")
             sys.exit(1)

    print("🎉 SECURITY VALIDATION PASSED")

if __name__ == "__main__":
    asyncio.run(test_access_control())
