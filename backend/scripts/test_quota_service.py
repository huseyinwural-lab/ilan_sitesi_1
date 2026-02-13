
import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, delete

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.services.quota_service import QuotaService, QuotaExceededError
from app.models.monetization import QuotaUsage

async def test_quota_flow():
    print("🚀 Starting Quota Service Test...")
    
    async with AsyncSessionLocal() as session:
        # Setup: Find a test user
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = res.scalar()
        if not user_id:
            print("❌ No user found")
            return

        print(f"User: {user_id}")
        service = QuotaService(session)
        
        # 1. Clear Usage
        await session.execute(delete(QuotaUsage).where(QuotaUsage.user_id == user_id))
        await session.commit()
        
        # 2. Check Free Limit (Default 3)
        print("Checking Limits (Free Plan)...")
        limits = await service.get_limits(user_id)
        print(f"Limits: {limits}")
        
        # 3. Consume 3 slots
        print("Consuming 3 slots...")
        try:
            for i in range(3):
                await service.consume_quota(user_id, "listing_active")
                print(f"Consumed {i+1}")
            await session.commit()
        except Exception as e:
            print(f"❌ Failed to consume: {e}")
            
        # 4. Try 4th (Should Fail)
        print("Attempting 4th (Over Limit)...")
        try:
            await service.consume_quota(user_id, "listing_active")
            print("❌ Error: Should have failed!")
        except QuotaExceededError as e:
            print(f"✅ Blocked as expected: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            
        await session.rollback()
        
        # 5. Release
        print("Releasing 1 slot...")
        await service.release_quota(user_id, "listing_active")
        await session.commit()
        
        usage = await service.get_usage(user_id, "listing_active")
        print(f"Usage after release: {usage}")
        
        # 6. Try Again (Should Succeed)
        print("Attempting 4th again (Slot free)...")
        try:
            await service.consume_quota(user_id, "listing_active")
            await session.commit()
            print("✅ Success!")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_quota_flow())
