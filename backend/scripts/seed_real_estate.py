import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

async def seed_real_estate():
    print("🏠 Seeding Real Estate Categories...")
    
    async with AsyncSessionLocal() as db:
        # 1. Root: Emlak
        root = await get_or_create(db, None, "real_estate", "Emlak", "Real Estate", "Immobilien", "building", "real_estate")
        
        # 2. Level 2: Segments
        l2_segments = [
            ("residential", "Konut", "Residential", "Wohnen", "home"),
            ("commercial", "Ticari", "Commercial", "Gewerbe", "briefcase"),
            ("short_term", "Günlük Kiralık", "Short-term", "Ferienwohnung", "calendar"),
            ("land", "Arsa", "Land", "Grundstück", "map")
        ]
        
        for key, tr, en, de, icon in l2_segments:
            l2 = await get_or_create(db, root.id, key, tr, en, de, icon, "real_estate")
            
            # 3. Level 3: Transaction Types
            # Logic: Short-term and Land might have different L3s
            if key == "short_term":
                # Short term usually doesn't have Sale/Rent split, it IS Rent.
                # We skip L3 or add a dummy 'daily' L3 to keep depth consistent if needed.
                # Let's map subtypes directly to L2 for short_term as per spec, 
                # BUT to keep "Search Filter" logic consistent (Transaction Type), 
                # we explicitly add a hidden or auto-selected L3.
                # Let's add subtypes directly to L2 for simplicity in this seed.
                await seed_subtypes(db, l2.id, get_residential_subtypes())
                
            elif key == "land":
                # Sale / Rent
                for t_key, t_tr, t_en, t_de in [("sale", "Satılık", "For Sale", "Verkauf"), ("rent", "Kiralık", "For Rent", "Mieten")]:
                    l3 = await get_or_create(db, l2.id, f"{key}_{t_key}", t_tr, t_en, t_de, None, "real_estate")
                    # Land Subtypes
                    await seed_subtypes(db, l3.id, [
                        ("residential_land", "İmarlı Konut", "Residential Land", "Bauland"),
                        ("commercial_land", "Ticari İmarlı", "Commercial Land", "Gewerbeland"),
                        ("agricultural", "Tarla", "Agricultural", "Ackerland")
                    ])
            else:
                # Residential & Commercial
                for t_key, t_tr, t_en, t_de in [("sale", "Satılık", "For Sale", "Verkauf"), ("rent", "Kiralık", "For Rent", "Mieten")]:
                    l3 = await get_or_create(db, l2.id, f"{key}_{t_key}", t_tr, t_en, t_de, None, "real_estate")
                    
                    if key == "residential":
                        await seed_subtypes(db, l3.id, get_residential_subtypes())
                    elif key == "commercial":
                        await seed_subtypes(db, l3.id, get_commercial_subtypes())

        await db.commit()
        print("✅ Real Estate Seeded.")

def get_residential_subtypes():
    return [
        ("apartment", "Daire", "Apartment", "Wohnung"),
        ("house", "Müstakil Ev", "Detached House", "Haus"),
        ("residence", "Rezidans", "Residence", "Residenz"),
        ("villa", "Villa", "Villa", "Villa"),
        ("farm_house", "Çiftlik Evi", "Farm House", "Bauernhaus"),
        ("summer_house", "Yazlık", "Summer House", "Sommerhaus")
    ]

def get_commercial_subtypes():
    return [
        ("office", "Ofis & Büro", "Office", "Büro"),
        ("retail", "Mağaza & Dükkan", "Retail", "Ladenfläche"),
        ("warehouse", "Depo", "Warehouse", "Lagerhalle"),
        ("factory", "Fabrika", "Factory", "Fabrik"),
        ("parking", "Otopark", "Parking", "Parkplatz"),
        ("plaza", "Plaza", "Plaza", "Plaza"),
        ("hotel", "Otel", "Hotel", "Hotel")
    ]

async def seed_subtypes(db, parent_id, subtypes):
    for key, tr, en, de in subtypes:
        await get_or_create(db, parent_id, key, tr, en, de, None, "real_estate")

async def get_or_create(db, parent_id, key, tr, en, de, icon, module):
    # Simple check by key (slug)
    # Note: Slug is stored as JSONB {"en": "...", "tr": "..."} in the model usually, 
    # but based on previous seeds, we might be creating slugs dynamically.
    # Let's assume schema from P28/P19.
    
    # We construct slug dict
    slug = {"tr": key, "en": key} 
    
    # Check
    # This is a basic check; real production might need recursive path check.
    # For MVP seed, we check if a category with this 'module' and 'slug' exists?
    # Actually Model has 'slug' as JSON. Searching inside JSON is dialect specific.
    # We will just fetch all and filter in python for this seed script to be safe.
    
    # Optimization: Filter by parent_id
    stmt = select(Category).where(Category.parent_id == parent_id)
    result = await db.execute(stmt)
    children = result.scalars().all()
    
    for c in children:
        # Check if translation matches roughly or key
        # Assuming we store 'key' or using slug as key
        if c.slug.get("en") == key or c.slug.get("tr") == key:
            return c
            
    # Create
    cat = Category(
        parent_id=parent_id,
        module=module,
        slug={"tr": key, "en": key}, # Using key as slug for simplicity in URLs
        icon=icon,
        is_enabled=True,
        sort_order=0
    )
    db.add(cat)
    await db.flush() # Get ID
    
    # Translations
    db.add(CategoryTranslation(category_id=cat.id, language="tr", name=tr))
    db.add(CategoryTranslation(category_id=cat.id, language="en", name=en))
    db.add(CategoryTranslation(category_id=cat.id, language="de", name=de))
    
    return cat

if __name__ == "__main__":
    asyncio.run(seed_real_estate())
