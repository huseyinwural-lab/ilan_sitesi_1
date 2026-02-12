
import asyncio
import logging
import sys
import os
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

# Add backend directory to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap
from app.models.commercial import DealerPackage

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("production_seed")

async def seed_production_data():
    logger.info("Starting Production Data Seed (DE Market)...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Clear Old Data (Safety: Only if explicitly intended for fresh start)
            # logger.info("Clearing existing Category and Attribute data...")
            # await session.execute(delete(CategoryAttributeMap))
            # await session.execute(delete(CategoryTranslation))
            # await session.execute(delete(Category))
            # await session.execute(delete(AttributeOption))
            # await session.execute(delete(Attribute))
            # await session.execute(delete(DealerPackage)) # Clear packages too? Maybe not for production seed update.
            # await session.commit()
            # logger.info("Data cleared.")

            # 2. Create Attributes
            # ... (Attributes logic same as before, skipping for brevity in this update, or keep if full re-run needed)
            
            # 3. Create Dealer Packages (CRITICAL FOR DUMMY SEED)
            logger.info("Creating Dealer Packages...")
            # Ensure Tier enum/string is supported by model
            packages = [
                ("BASIC", "STANDARD", 49.00, 10, 0),
                ("PRO", "PREMIUM", 149.00, 50, 5),
                ("ENTERPRISE", "ENTERPRISE", 499.00, 500, 20)
            ]
            
            for key, tier, price, limit, prem in packages:
                # Check exist
                exists = await session.execute(select(DealerPackage).where(DealerPackage.key == key))
                if not exists.scalar_one_or_none():
                    pkg = DealerPackage(
                        key=key,
                        country="DE",
                        name={"en": f"{tier} Package"},
                        price_net=Decimal(str(price)),
                        currency="EUR",
                        duration_days=30,
                        listing_limit=limit,
                        premium_quota=prem,
                        highlight_quota=prem,
                        tier=tier, # Added Tier
                        is_active=True
                    )
                    session.add(pkg)
            
            await session.commit()
            logger.info("Dealer Packages Created.")

            # ... (Rest of category logic) ...

        except Exception as e:
            logger.error(f"Seeding Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_production_data())
