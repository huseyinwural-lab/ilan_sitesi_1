
import asyncio
import logging
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("re_cat_seed")

async def seed_real_estate_categories():
    """Add Real Estate categories without deleting existing data"""
    logger.info("🏠 Adding Real Estate Categories...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if real estate already exists
            existing = await session.execute(
                select(Category).where(Category.module == 'real_estate')
            )
            if existing.scalars().first():
                logger.info("✅ Real Estate categories already exist. Skipping.")
                return

            # Helper to create category
            async def create_cat(module, slug_en, name_en, name_de, name_tr, icon, parent=None):
                cat = Category(
                    module=module,
                    parent_id=parent.id if parent else None,
                    slug={"en": slug_en, "de": slug_en, "tr": slug_en},
                    icon=icon,
                    is_enabled=True,
                    is_visible_on_home=True,
                    allowed_countries=["DE", "AT", "CH", "FR", "TR"]
                )
                session.add(cat)
                await session.flush()
                
                # Add translations
                session.add(CategoryTranslation(category_id=cat.id, language="en", name=name_en))
                session.add(CategoryTranslation(category_id=cat.id, language="de", name=name_de))
                session.add(CategoryTranslation(category_id=cat.id, language="tr", name=name_tr))
                
                # Update path
                cat.path = f"{parent.path}.{cat.id}" if parent else str(cat.id)
                cat.depth = (parent.depth + 1) if parent else 0
                
                return cat

            # --- REAL ESTATE ---
            cat_re = await create_cat("real_estate", "real-estate", "Real Estate", "Immobilien", "Emlak", "building-2")
            
            # Housing
            cat_housing = await create_cat("real_estate", "housing", "Housing", "Wohnen", "Konut", "home", cat_re)
            await create_cat("real_estate", "apartment-sale", "Apartment for Sale", "Wohnung kaufen", "Satılık Daire", "key", cat_housing)
            await create_cat("real_estate", "apartment-rent", "Apartment for Rent", "Mietwohnung", "Kiralık Daire", "key", cat_housing)
            await create_cat("real_estate", "house-sale", "House for Sale", "Haus kaufen", "Satılık Ev", "home", cat_housing)
            await create_cat("real_estate", "house-rent", "House for Rent", "Haus mieten", "Kiralık Ev", "home", cat_housing)

            # Commercial
            cat_comm = await create_cat("real_estate", "commercial", "Commercial", "Gewerbe", "İşyeri", "briefcase", cat_re)
            await create_cat("real_estate", "office", "Office & Praxis", "Büro & Praxis", "Ofis", "monitor", cat_comm)
            await create_cat("real_estate", "retail", "Retail", "Einzelhandel", "Mağaza", "shopping-bag", cat_comm)
            await create_cat("real_estate", "warehouse", "Warehouse", "Lagerhalle", "Depo", "warehouse", cat_comm)

            await session.commit()
            logger.info("✅ Real Estate categories created successfully.")

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_real_estate_categories())
