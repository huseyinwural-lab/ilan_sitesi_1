
import asyncio
import sys
import os
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.vehicle_mdm import VehicleMake, VehicleModel

async def audit_vehicle_integrity():
    print("🕵️ Auditing Vehicle Master Data Integrity...")
    
    async with AsyncSessionLocal() as session:
        # 1. Null Checks
        res = await session.execute(select(Listing).where(
            Listing.module == 'vehicle',
            (Listing.make_id == None) | (Listing.model_id == None)
        ))
        nulls = res.scalars().all()
        if nulls:
            print(f"❌ FAIL: Found {len(nulls)} listings with NULL Make/Model.")
        else:
            print("✅ PASS: All vehicle listings have Make/Model IDs.")

        # 2. Cross Check
        # Check if listing.model_id actually belongs to listing.make_id
        # We need to join.
        # ORM way:
        stmt = select(Listing, VehicleModel).join(VehicleModel, Listing.model_id == VehicleModel.id).where(
            Listing.module == 'vehicle',
            Listing.make_id != VehicleModel.make_id
        )
        res = await session.execute(stmt)
        mismatches = res.all()
        
        if mismatches:
            print(f"❌ FAIL: Found {len(mismatches)} listings where Model does not belong to Make.")
            for l, m in mismatches:
                print(f"   -> Listing {l.id}: Make {l.make_id} vs Model Parent {m.make_id}")
        else:
            print("✅ PASS: All listings have consistent Make/Model relationship.")

        # 3. Orphan Check
        stmt = select(VehicleModel).where(VehicleModel.make_id.not_in(select(VehicleMake.id)))
        res = await session.execute(stmt)
        orphans = res.scalars().all()
        
        if orphans:
             print(f"❌ FAIL: Found {len(orphans)} orphan models.")
        else:
             print("✅ PASS: No orphan models found.")

if __name__ == "__main__":
    asyncio.run(audit_vehicle_integrity())
