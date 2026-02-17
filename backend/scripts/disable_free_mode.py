import asyncio
import sys
import os
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.core import FeatureFlag

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

async def disable_free_mode():
    print("🔒 Disabling Global Free Mode (Phase Out)...")
    
    async with AsyncSessionLocal() as db:
        # 1. Disable Feature Flag
        stmt = select(FeatureFlag).where(FeatureFlag.key == "monetization_free_mode")
        flag = (await db.execute(stmt)).scalar_one_or_none()
        
        if flag:
            flag.is_enabled = False
            await db.commit()
            print("✅ Feature Flag Disabled.")
        else:
            print("⚠️ Flag not found.")
            
        # 2. Trigger Quota Re-calc (Mock)
        # In prod: Enqueue a Celery task to check all users and expire listings
        print("ℹ️ Quota enforcement will apply on next listing submission.")

if __name__ == "__main__":
    asyncio.run(disable_free_mode())
