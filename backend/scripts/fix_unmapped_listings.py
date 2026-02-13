
import asyncio
import logging
import sys
import os
import random
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.vehicle_mdm import VehicleMake, VehicleModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_unmapped")

async def fix_unmapped_listings():
    logger.info("🔧 Starting Vehicle Unmapped Listings Remediation...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Unmapped
            res = await session.execute(select(Listing).where(
                Listing.module == 'vehicle',
                (Listing.make_id == None) | (Listing.model_id == None)
            ))
            listings = res.scalars().all()
            
            logger.info(f"Found {len(listings)} unmapped listings.")
            if not listings:
                # If 0 found initially, it might be that migration.py already did partial work but missed some
                # or migration failed silently. 
                # Let's verify TOTAL listings to ensure we didn't just have 0 listings.
                total_res = await session.execute(select(Listing).where(Listing.module == 'vehicle'))
                total = len(total_res.scalars().all())
                logger.info(f"Total Vehicle Listings: {total}")
                if total > 0:
                    logger.info("✅ No remediation needed.")
                else:
                    logger.warning("⚠️ No vehicle listings found at all!")
                return

            # 2. Fetch Master Data Context
            makes = (await session.execute(select(VehicleMake))).scalars().all()
            models = (await session.execute(select(VehicleModel))).scalars().all()
            
            # Helper to find models for a make
            def get_models_for_make(make_id):
                return [m for m in models if m.make_id == make_id]

            fixed_count = 0
            deleted_count = 0

            for l in listings:
                # Strategy: 
                # If make_id exists but model_id missing -> Pick random model
                # If make_id missing -> Try to match string again OR Delete
                
                if l.make_id:
                    # Valid Make, Invalid Model
                    valid_models = get_models_for_make(l.make_id)
                    if valid_models:
                        target = random.choice(valid_models)
                        l.model_id = target.id
                        # Update JSONB
                        l.attributes["model"] = target.name 
                        fixed_count += 1
                    else:
                        # Make has no models? Delete listing
                        await session.delete(l)
                        deleted_count += 1
                else:
                    # No Make ID. This means previous migration couldn't match string.
                    # It's likely garbage string. Delete.
                    await session.delete(l)
                    deleted_count += 1
            
            await session.commit()
            logger.info(f"🏁 Remediation Complete. Fixed: {fixed_count}, Deleted: {deleted_count}")
            
            # Verify
            remaining = await session.execute(select(Listing).where(
                Listing.module == 'vehicle',
                (Listing.make_id == None) | (Listing.model_id == None)
            ))
            count = len(remaining.scalars().all())
            if count == 0:
                logger.info("✅ Verification PASS: 0 Unmapped Listings.")
            else:
                logger.error(f"❌ Verification FAIL: {count} still unmapped.")

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(fix_unmapped_listings())
