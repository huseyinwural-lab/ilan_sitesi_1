
import asyncio
import os
import sys
import httpx
import uuid
from sqlalchemy import text

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.user import User, SignupAllowlist
from server import create_access_token

async def test_invite_flow():
    print("🚀 Starting Invite-Only Flow Test...")
    
    admin_email = "admin@platform.com"
    target_email = f"invited_user_{uuid.uuid4().hex[:6]}@example.com"
    
    # 1. Setup Admin Token
    # Assuming admin exists (seeded). If not, we create one or mock token.
    # We can just create a token with super_admin role manually.
    async with AsyncSessionLocal() as session:
        # Get Admin ID
        res = await session.execute(text(f"SELECT id FROM users WHERE email = '{admin_email}'"))
        admin_id = res.scalar()
        if not admin_id:
            # Fallback
            admin_id = uuid.uuid4()
            # We don't need real admin in DB if we fake the token, 
            # BUT the endpoint checks `current_user` in DB.
            # So we MUST have a user in DB.
            print("❌ Admin user not found. Seeding admin...")
            await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified) VALUES ('{admin_id}', '{admin_email}', 'hash', 'Admin', 'super_admin', true, true)"))
            await session.commit()
    
    token = create_access_token({"sub": str(admin_id), "email": admin_email, "role": "super_admin"})
    admin_headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        base_url = "http://localhost:8001/api"
        
        # 2. Try Register (Should Fail)
        print("\n🔹 Testing Blocked Registration...")
        reg_data = {
            "email": target_email,
            "password": "password123",
            "full_name": "Test User",
            "country_scope": ["DE"],
            "preferred_language": "en"
        }
        resp = await client.post(f"{base_url}/auth/register", json=reg_data)
        
        if resp.status_code == 403:
            print("✅ Blocked successfully (403 Forbidden)")
        else:
            print(f"❌ Failed to block! Status: {resp.status_code}, Body: {resp.text}")
            return

        # 3. Add to Allowlist (Admin)
        print("\n🔹 Adding to Allowlist...")
        allow_data = {"email": target_email}
        resp = await client.post(f"http://localhost:8001/api/v1/admin/allowlist", json=allow_data, headers=admin_headers)
        
        if resp.status_code == 201:
            print("✅ Added to allowlist")
        else:
            print(f"❌ Failed to add to allowlist: {resp.text}")
            return

        # 4. Try Register Again (Should Succeed)
        print("\n🔹 Testing Allowed Registration...")
        resp = await client.post(f"{base_url}/auth/register", json=reg_data)
        
        if resp.status_code == 201:
            print("✅ Registration Successful")
        else:
            print(f"❌ Registration Failed! Status: {resp.status_code}, Body: {resp.text}")
            return
            
    # 5. Verify DB Flag
    async with AsyncSessionLocal() as session:
        res = await session.execute(text(f"SELECT is_used FROM signup_allowlist WHERE email = '{target_email}'"))
        is_used = res.scalar()
        if is_used:
            print("✅ 'is_used' flag set to True")
        else:
            print("❌ 'is_used' flag NOT set!")

    print("\n🎉 Invite-Only Flow PASSED!")

if __name__ == "__main__":
    asyncio.run(test_invite_flow())
