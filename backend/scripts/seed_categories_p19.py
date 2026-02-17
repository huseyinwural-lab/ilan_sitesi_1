import asyncio
import sys
import os
from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def seed():
    print("Seeding categories...")
    async with AsyncSessionLocal() as db:
        # Check if "cars" exists
        # We'll just fetch all and check manually in python to avoid JSON query complexity
        result = await db.execute(select(Category))
        categories = result.scalars().all()
        
        cars_exists = False
        for c in categories:
            if c.slug.get('en') == 'cars':
                cars_exists = True
                break
        
        if not cars_exists:
            print("Creating 'cars' category...")
            cat = Category(
                module="vehicle",
                slug={"en": "cars", "tr": "arabalar", "de": "autos"},
                icon="car",
                is_enabled=True,
                sort_order=1
            )
            db.add(cat)
            await db.flush()
            
            # Translations
            db.add(CategoryTranslation(category_id=cat.id, language="en", name="Cars"))
            db.add(CategoryTranslation(category_id=cat.id, language="tr", name="Arabalar"))
            db.add(CategoryTranslation(category_id=cat.id, language="de", name="Autos"))
            
            await db.commit()
            print("Seeded 'cars' category.")
        else:
            print("'cars' category already exists.")

if __name__ == "__main__":
    asyncio.run(seed())
