
import asyncio
import asyncpg
import os
import random
import uuid
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scale_50k")

# Database Config
DB_DSN = os.environ.get("DATABASE_URL", "postgresql://admin_user:admin_pass@localhost:5432/admin_panel").replace('+asyncpg', '')

TARGET_TOTAL = 50000
BATCH_SIZE = 5000

# Distribution
CATS = {
    "cars": {"ratio": 0.6, "attrs": 12},
    "real_estate": {"ratio": 0.2, "attrs": 8},
    "shopping": {"ratio": 0.1, "attrs": 5},
    "others": {"ratio": 0.1, "attrs": 3}
}

async def fetch_ids(conn, table):
    return [r['id'] for r in await conn.fetch(f"SELECT id FROM {table}")]

async def scale_data():
    conn = await asyncpg.connect(DB_DSN)
    logger.info("🔌 Connected to DB")

    try:
        # 1. Fetch Context
        user_ids = await fetch_ids(conn, "users")
        cat_rows = await conn.fetch("SELECT id, slug, module FROM categories")
        # asyncpg returns Record objects, accessing JSON field needs json.loads if it comes as string, 
        # but asyncpg usually decodes JSONB automatically. 
        # However, error "string indices must be integers" suggests r['slug'] might be a string.
        # Let's inspect or use json.loads just in case if it's text.
        cats = {}
        for r in cat_rows:
            slug_val = r['slug']
            if isinstance(slug_val, str):
                try:
                    slug_val = json.loads(slug_val)
                except:
                    pass
            if isinstance(slug_val, dict):
                cats[slug_val.get('en', 'unknown')] = r['id']
        
        # Ensure we have users
        if not user_ids:
            logger.error("No users found. Run seed_dummy_users.py first.")
            return

        # 2. Prepare Data Generators
        now = datetime.utcnow()
        
        async def insert_listings(target_cat_slug, count, attr_count):
            cat_id = cats.get(target_cat_slug)
            if not cat_id: 
                # Fallback to any category in module if exact slug not found
                # Simplified for script
                cat_id = list(cats.values())[0]

            logger.info(f"Generating {count} listings for {target_cat_slug}...")
            
            listings = []
            listing_attrs = []
            
            for _ in range(count):
                lid = uuid.uuid4()
                uid = random.choice(user_ids)
                price = random.randint(1000, 5000000)
                
                # Listing Row
                listings.append((
                    lid,
                    f"Load Test Item {random.randint(1000,9999)} - {target_cat_slug}", # title
                    "Generated for 50k load test.", # description
                    "vehicle" if "car" in target_cat_slug else "real_estate", # module (simplified)
                    cat_id,
                    "TR", # country
                    "Istanbul", # city
                    price,
                    "TRY",
                    uid,
                    "active",
                    now - timedelta(days=random.randint(0, 60)), # created_at
                    json.dumps([f"https://picsum.photos/seed/{lid}/800/600"]) # images
                ))
                
                # Simplified Attributes (We don't join EAV for this raw speed test, but we populate table)
                # In real scenario we'd map to real attribute definitions. 
                # Here we just want volume in listing_attributes to stress test joins.
                # We need valid attribute_ids.
                
            # Bulk Insert Listings
            # We need to map columns to tuple order
            # Row: (id, title, desc, module, cat_id, country, city, price, currency, user_id, status, created_at, images)
            # Table has: is_dealer_listing (bool), is_premium (bool) which are NOT NULL or default.
            # copy_records_to_table expects columns to match data.
            # Let's add is_dealer_listing=False, is_premium=False
            
            records_with_defaults = []
            for r in listings:
                # r is tuple of 13 items
                # add is_dealer_listing (False), is_premium (False), image_count (1)
                records_with_defaults.append(r + (False, False, 1))

            await conn.copy_records_to_table(
                'listings',
                records=records_with_defaults,
                columns=['id', 'title', 'description', 'module', 'category_id', 'country', 'city', 'price', 'currency', 'user_id', 'status', 'created_at', 'images', 'is_dealer_listing', 'is_premium', 'image_count']
            )
            logger.info(f"✅ Inserted {count} listings")

        # 3. Execution
        # Cars
        await insert_listings("cars", int(TARGET_TOTAL * CATS['cars']['ratio']), 12)
        # Real Estate
        await insert_listings("flats", int(TARGET_TOTAL * CATS['real_estate']['ratio']), 8)
        # Others
        await insert_listings("electronics", int(TARGET_TOTAL * 0.2), 5) # Combine others

        # 4. Update Stats
        total = await conn.fetchval("SELECT count(*) FROM listings")
        logger.info(f"🎉 Total Listings: {total}")
        
        # Analyze
        await conn.execute("ANALYZE listings")
        await conn.execute("ANALYZE listing_attributes")

    finally:
        await conn.close()

if __name__ == "__main__":
    # pip install asyncpg
    asyncio.run(scale_data())
