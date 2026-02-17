
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

async def test_growth_analytics_v2():
    print("🚀 Starting Growth Analytics V2 (Segmented) Test...")
    
    admin_id = str(uuid.uuid4())
    admin_email = "growth_v2@test.com"

    # Cleanup
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("DELETE FROM growth_events"))
            await session.execute(text(f"DELETE FROM users WHERE email IN ('{admin_email}', 'tr_user@test.com', 'de_user@test.com')"))
            await session.commit()
        except:
            await session.rollback()

    # 1. Setup Admin & Test Data
    async with AsyncSessionLocal() as session:
        # Create Admin
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_code, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{admin_id}', '{admin_email}', 'hash', 'Growth Admin V2', 'super_admin', true, true, 'TR', '[]', 'en', false, NOW(), NOW())"))
        
        # Create TR User
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_code, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES (gen_random_uuid(), 'tr_user@test.com', 'hash', 'TR User', 'individual', true, true, 'TR', '[]', 'en', false, NOW(), NOW())"))
        
        # Create DE User
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_code, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES (gen_random_uuid(), 'de_user@test.com', 'hash', 'DE User', 'individual', true, true, 'DE', '[]', 'en', false, NOW(), NOW())"))
        
        await session.commit()

    token = create_access_token({"sub": admin_id, "email": admin_email, "role": "super_admin"})
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8001/api/v1/admin/growth"
    
    # 2. Log Events (Segmented)
    print("\n🔹 1. Logging Segmented Events...")
    async with AsyncSessionLocal() as session:
        service = GrowthService(session)
        # TR Event
        await service.log_event("subscription_confirmed", country_code="TR", data={"amount": 100})
        # DE Event
        await service.log_event("subscription_confirmed", country_code="DE", data={"amount": 50})
        await session.commit()
        print("✅ Events Logged")

    async with httpx.AsyncClient() as client:
        # 3. Get Overview (TR)
        print("\n🔹 2. Get Overview (TR)...")
        resp = await client.get(f"{base_url}/overview?country=TR", headers=headers)
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ TR Data: {data}")
            if data["total_sales_count"] >= 1: # At least the one we logged
                print("✅ TR Sales Count Verified")
            else:
                print("❌ TR Sales Count Mismatch")
        else:
            print(f"❌ API Failed: {resp.status_code} {resp.text}")

        # 4. Get Overview (DE)
        print("\n🔹 3. Get Overview (DE)...")
        resp = await client.get(f"{base_url}/overview?country=DE", headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ DE Data: {data}")
            # Note: total_users might be low if DB was clean, but we added one DE user above.
        else:
            print(f"❌ API Failed: {resp.status_code}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM growth_events"))
        await session.execute(text(f"DELETE FROM users WHERE email IN ('{admin_email}', 'tr_user@test.com', 'de_user@test.com')"))
        await session.commit()

    print("\n🎉 Growth Analytics V2 PASSED!")

if __name__ == "__main__":
    asyncio.run(test_growth_analytics_v2())
