import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.core import FeatureFlag

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

async def enable_free_mode():
    print("🆓 Enabling Global Free Mode...")
    
    async with AsyncSessionLocal() as db:
        # Check if flag exists
        stmt = select(FeatureFlag).where(FeatureFlag.key == "monetization_free_mode")
        flag = (await db.execute(stmt)).scalar_one_or_none()
        
        if not flag:
            flag = FeatureFlag(
                key="monetization_free_mode",
                name={"en": "Global Free Mode"},
                scope="global",
                is_enabled=True,
                description={"en": "Overrides quotas for growth"}
            )
            db.add(flag)
        else:
            flag.is_enabled = True
            
        await db.commit()
        print("✅ Free Mode Activated.")

if __name__ == "__main__":
    asyncio.run(enable_free_mode())
