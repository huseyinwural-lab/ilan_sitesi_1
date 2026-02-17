
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.growth import GrowthEvent
from app.models.user import User
from app.services.growth_service import GrowthService
from server import create_access_token

async def test_growth_analytics():
    print("🚀 Starting Growth Analytics Test...")
    
    admin_id = str(uuid.uuid4())
    admin_email = "growth_admin@test.com"
    
    # 1. Setup Admin
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{admin_id}', '{admin_email}', 'hash', 'Growth Admin', 'super_admin', true, true, '[]', 'en', false, NOW(), NOW())"))
        await session.commit()

    token = create_access_token({"sub": admin_id, "email": admin_email, "role": "super_admin"})
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8001/api/v1/admin/growth"
    
    # 2. Log Events (Direct Service Call to simulate traffic)
    print("\n🔹 1. Logging Events...")
    async with AsyncSessionLocal() as session:
        service = GrowthService(session)
        await service.log_event("user_registered", user_id=admin_id)
        await service.log_event("subscription_confirmed", user_id=admin_id, data={"amount": 100})
        await session.commit()
        print("✅ Events Logged")

    async with httpx.AsyncClient() as client:
        # 3. Get Overview
        print("\n🔹 2. Get Overview...")
        resp = await client.get(f"{base_url}/overview", headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Overview Data: {data}")
            if data["total_sales_count"] >= 1:
                print("✅ Sales Count Verified")
            else:
                print("❌ Sales Count Mismatch")
        else:
            print(f"❌ API Failed: {resp.status_code} {resp.text}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM growth_events"))
        await session.execute(text(f"DELETE FROM users WHERE id = '{admin_id}'"))
        await session.commit()

    print("\n🎉 Growth Analytics PASSED!")

if __name__ == "__main__":
    asyncio.run(test_growth_analytics())
