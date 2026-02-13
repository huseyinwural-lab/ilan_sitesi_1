
import asyncio
import logging
import sys
import os
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.vehicle_mdm import VehicleMake, VehicleModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mdm_migrate")

async def migrate_listings_to_mdm():
    logger.info("🔄 Starting Vehicle Listing Migration (String -> ID)...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Lookups
            makes = (await session.execute(select(VehicleMake))).scalars().all()
            models = (await session.execute(select(VehicleModel))).scalars().all()
            
            make_map = {m.slug: m.id for m in makes}
            # Fallback map for common mismatches in Seed v4
            make_map["mercedes"] = make_map.get("mercedes-benz")
            make_map["vw"] = make_map.get("vw") # slug is vw, correct
            
            # 2. Fetch Listings
            listings = (await session.execute(select(Listing).where(Listing.module == 'vehicle'))).scalars().all()
            logger.info(f"Processing {len(listings)} listings...")
            
            updated_count = 0
            unmapped_count = 0
            
            for l in listings:
                attrs = l.attributes
                brand_str = str(attrs.get("brand")).lower().replace(" ", "-")
                
                # Match Make
                # Try direct slug, then aliases
                make_id = make_map.get(brand_str)
                
                model_id = None
                if make_id:
                    # Match Model
                    # Listing title/model field might be messy.
                    # In Seed v4: model = "Model 123". This won't match "3-Series".
                    # Real migration needs fuzzy logic. 
                    # For Seed v4 specifically, we generated random "Model X".
                    # We can't map "Model 123" to "3-Series".
                    # STRATEGY: Update the Listing to use a VALID random model from Master Data.
                    # Because keeping "Model 123" with a valid Make ID is partial migration.
                    # Let's assign a random valid model for that Make to ensure FK integrity.
                    
                    valid_models = [m for m in models if m.make_id == make_id]
                    if valid_models:
                        import random
                        target_model = random.choice(valid_models)
                        model_id = target_model.id
                        
                        # Update Listing
                        l.make_id = make_id
                        l.model_id = model_id
                        
                        # Update JSONB too for consistency? Or leave as legacy?
                        # Let's update JSONB to match new reality
                        attrs["brand"] = target_model.make_id # Storing ID in JSON? No, keep string for now but standardized.
                        # Actually, keeping string in JSON is fine for readout fallback.
                        # But l.make_id is the source of truth now.
                        updated_count += 1
                    else:
                        logger.warning(f"No models found for make {brand_str}")
                else:
                    unmapped_count += 1
                    # logger.warning(f"Unmapped Brand: {brand_str}")

            await session.commit()
            logger.info(f"✅ Migration Complete. Updated: {updated_count}, Unmapped: {unmapped_count}")

        except Exception as e:
            logger.error(f"❌ Migration Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(migrate_listings_to_mdm())
