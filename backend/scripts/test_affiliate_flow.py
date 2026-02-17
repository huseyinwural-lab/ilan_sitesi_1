
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.affiliate import Affiliate
from server import create_access_token

async def test_affiliate_flow():
    print("🚀 Starting Affiliate Flow Test...")
    
    user_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    email = f"aff_{user_id[:8]}@test.com"
    admin_email = "admin@platform.com" # Assuming exists or we create
    
    # 1. Setup User
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{user_id}', '{email}', 'hash', 'Affiliate Candidate', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        
        # Ensure Admin
        res = await session.execute(text(f"SELECT id FROM users WHERE email = '{admin_email}'"))
        existing_admin_id = res.scalar()
        if not existing_admin_id:
             await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{admin_id}', '{admin_email}', 'hash', 'Admin', 'super_admin', true, true, '[]', 'en', false, NOW(), NOW())"))
        else:
             admin_id = existing_admin_id # Use existing
             
        await session.commit()

    user_token = create_access_token({"sub": user_id, "email": email, "role": "individual"})
    admin_token = create_access_token({"sub": str(admin_id), "email": admin_email, "role": "super_admin"})
    
    base_url = "http://localhost:8001/api/v1"
    
    async with httpx.AsyncClient() as client:
        # 2. Apply
        print("\n🔹 1. User Apply...")
        headers = {"Authorization": f"Bearer {user_token}"}
        payload = {
            "custom_slug": "super-affiliate",
            "payout_details": {"iban": "TR123456"}
        }
        resp = await client.post(f"{base_url}/affiliate/apply", json=payload, headers=headers)
        
        if resp.status_code == 201:
            print("✅ Applied successfully")
        else:
            print(f"❌ Apply Failed: {resp.text}")
            return

        # 3. Admin List
        print("\n🔹 2. Admin List Pending...")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        resp = await client.get(f"{base_url}/admin/affiliates?status=pending", headers=admin_headers)
        apps = resp.json()
        target_app = next((a for a in apps if a["slug"] == "super-affiliate"), None)
        
        if target_app:
            print(f"✅ Application found: {target_app['id']}")
        else:
            print("❌ Application NOT found in admin list")
            return

        # 4. Admin Approve
        print("\n🔹 3. Admin Approve...")
        review_payload = {"action": "approve"}
        resp = await client.post(f"{base_url}/admin/affiliates/{target_app['id']}/review", json=review_payload, headers=admin_headers)
        
        if resp.status_code == 200:
            print("✅ Approved")
        else:
            print(f"❌ Approve Failed: {resp.text}")
            return

        # 5. Verify User Status
        print("\n🔹 4. Verify Status...")
        resp = await client.get(f"{base_url}/affiliate/me", headers=headers)
        data = resp.json()
        
        if data["status"] == "approved":
            print("✅ User status is APPROVED")
            print(f"   Link: {data['link']}")
        else:
            print(f"❌ Status Check Failed: {data}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM affiliates WHERE user_id = '{user_id}'"))
        await session.execute(text(f"DELETE FROM users WHERE id = '{user_id}'"))
        await session.commit()

    print("\n🎉 Affiliate Flow PASSED!")

if __name__ == "__main__":
    asyncio.run(test_affiliate_flow())
