
import asyncio
import os
import sys
import uuid
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, delete, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.monetization import QuotaUsage
from app.services.quota_service import QuotaService, QuotaExceededError

async def simulate_concurrent_create(user_id, count):
    print(f"🔥 Starting Stress Test: {count} Concurrent Creates for User {user_id}")
    
    success = 0
    blocked = 0
    errors = 0
    
    async def worker(i):
        nonlocal success, blocked, errors
        async with AsyncSessionLocal() as session:
            service = QuotaService(session)
            try:
                # Mimic Route Logic: Transactional Consume
                async with session.begin():
                    # Just consume quota, skip actual listing insert for speed/simplicity
                    await service.consume_quota(user_id, "listing_active", 1)
                # print(f"  Worker {i}: ✅ Success")
                success += 1
            except QuotaExceededError:
                # print(f"  Worker {i}: ⛔ Blocked")
                blocked += 1
            except Exception as e:
                print(f"  Worker {i}: ❌ Error {e}")
                errors += 1

    # Run concurrently
    tasks = [worker(i) for i in range(count)]
    await asyncio.gather(*tasks)
    
    print("\n--- Stress Test Results ---")
    print(f"Total Requests: {count}")
    print(f"✅ Success (Consumed): {success}")
    print(f"⛔ Blocked (Quota Limit): {blocked}")
    print(f"❌ System Errors: {errors}")
    
    return success, blocked

async def run_test():
    async with AsyncSessionLocal() as session:
        # 1. Setup User & Clear Quota
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = str(res.scalar())
        
        await session.execute(delete(QuotaUsage).where(QuotaUsage.user_id == user_id))
        await session.commit()
        
        print(f"Test User: {user_id}")
        
        # 2. Assert Free Limit is 3
        # We expect 3 successes, 17 blocks
        s, b = await simulate_concurrent_create(user_id, 20)
        
        # 3. Validation
        usage_res = await session.execute(select(QuotaUsage).where(QuotaUsage.user_id == user_id))
        usage = usage_res.scalar_one_or_none()
        final_used = usage.used if usage else 0
        
        print(f"\nFinal DB Usage Count: {final_used}")
        
        if s == 3 and b == 17 and final_used == 3:
            print("✅ TEST PASSED: Exact enforcement under concurrency.")
        else:
            print("❌ TEST FAILED: Leakage detected!")
            print(f"Expected: 3 Success, 17 Blocked. Got: {s} S, {b} B")

if __name__ == "__main__":
    asyncio.run(run_test())
