
import asyncio
import sys
import os
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing

async def uat_real_estate_verification():
    print("🕵️ UAT: Real Estate v3 Verification")
    async with AsyncSessionLocal() as session:
        # 1. Data Quality
        res = await session.execute(select(Listing).where(Listing.title.like("Test Listing%")))
        legacy = res.scalars().all()
        if len(legacy) > 0:
            print(f"❌ UAT-RE-001 FAIL: Found {len(legacy)} legacy listings!")
        else:
            print("✅ UAT-RE-001 PASS: No legacy data found.")

        # 2. Room Filter (3 Rooms)
        # Emulate Filter Logic: Fetch all, filter in python to verify data existence
        res = await session.execute(select(Listing).where(Listing.module == "real_estate"))
        listings = res.scalars().all()
        
        rooms_3 = [l for l in listings if str(l.attributes.get("room_count")) == "3"]
        print(f"   -> Found {len(rooms_3)} listings with 3 Rooms.")
        if len(rooms_3) > 0:
            print("✅ UAT-RE-002 PASS: Room filter candidates exist.")
        else:
            print("⚠️ UAT-RE-002 WARNING: No 3-room listings found (Check seed distribution).")

        # 3. Kitchen Filter
        kitchen_yes = [l for l in listings if l.attributes.get("has_kitchen") is True]
        print(f"   -> Found {len(kitchen_yes)} listings with Kitchen.")
        if len(kitchen_yes) > 0:
            print("✅ UAT-RE-003 PASS: Kitchen filter candidates exist.")
        else:
            print("❌ UAT-RE-003 FAIL: No kitchens found!")

        # 4. Commercial Isolation
        commercials = [l for l in listings if "ceiling_height" in l.attributes]
        errors = 0
        for c in commercials:
            if "has_kitchen" in c.attributes or "bathroom_count" in c.attributes:
                errors += 1
        
        if errors == 0 and len(commercials) > 0:
            print(f"✅ UAT-RE-004 PASS: {len(commercials)} commercial listings checked. Isolation perfect.")
        else:
            print(f"❌ UAT-RE-004 FAIL: {errors} commercial listings have residential attributes!")

if __name__ == "__main__":
    asyncio.run(uat_real_estate_verification())
