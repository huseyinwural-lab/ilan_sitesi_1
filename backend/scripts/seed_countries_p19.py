
import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

async def seed_countries():
    print("🚀 Seeding Countries & Updating Data...")
    
    countries = [
        {"code": "TR", "name": "Türkiye", "currency": "TRY", "lang": "tr"},
        {"code": "DE", "name": "Germany", "currency": "EUR", "lang": "de"},
        {"code": "FR", "name": "France", "currency": "EUR", "lang": "fr"},
    ]
    
    async with AsyncSessionLocal() as session:
        # 1. Update Countries Table (Upsert)
        for c in countries:
            # Check if exists
            res = await session.execute(text(f"SELECT id FROM countries WHERE code = '{c['code']}'"))
            if not res.scalar():
                # Provide default values for required fields like area_unit etc. if they exist in schema
                # Assuming schema from previous migrations might require them.
                # Let's check Country model or just provide safe defaults.
                await session.execute(text(f"INSERT INTO countries (id, code, name, default_currency, default_language, is_enabled, created_at, updated_at, area_unit, distance_unit, weight_unit, date_format, number_format) VALUES (gen_random_uuid(), '{c['code']}', '{{\"en\": \"{c['name']}\"}}', '{c['currency']}', '{c['lang']}', true, NOW(), NOW(), 'sqm', 'km', 'kg', 'DD/MM/YYYY', '.,')"))
                print(f"➕ Added Country: {c['code']}")
            else:
                print(f"ℹ️ Country Exists: {c['code']}")
        
        # 2. Backfill Listings (Assume TR if null or mismatch)
        # Listings already have 'country' column, we just indexed it.
        # But let's ensure normalization.
        await session.execute(text("UPDATE listings SET country = 'TR' WHERE country IS NULL"))
        
        # 3. Backfill Users (Set default TR)
        # We added country_code with server_default='TR', so new column is filled.
        # But let's ensure consistency.
        await session.execute(text("UPDATE users SET country_code = 'TR' WHERE country_code IS NULL"))
        
        await session.commit()
        print("✅ Country Data Synced.")

if __name__ == "__main__":
    asyncio.run(seed_countries())
