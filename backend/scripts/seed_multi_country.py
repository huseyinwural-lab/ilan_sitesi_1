
import asyncio
import os
import sys
import uuid
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.category import Category
from app.models.moderation import Listing
from app.models.core import Country

async def seed_multi_country_data():
    print("🚀 Seeding Multi-Country Data...")
    
    async with AsyncSessionLocal() as session:
        # 1. Ensure Countries (TR, DE)
        await session.execute(text("INSERT INTO countries (id, code, name, default_currency, default_language, is_enabled, created_at, updated_at, area_unit, distance_unit, weight_unit, date_format, number_format) VALUES (gen_random_uuid(), 'DE', '{\"en\": \"Germany\"}', 'EUR', 'de', true, NOW(), NOW(), 'sqm', 'km', 'kg', 'DD.MM.YYYY', ',.') ON CONFLICT (code) DO NOTHING"))
        
        # 2. Ensure Category
        cat_id = str(uuid.uuid4())
        await session.execute(text(f"INSERT INTO categories (id, module, slug, is_enabled, sort_order, created_at, updated_at, path, depth, is_visible_on_home, is_deleted, inherit_enabled, inherit_countries, allowed_countries, listing_count) VALUES ('{cat_id}', 'vehicle', '{{\"en\": \"cars\", \"tr\": \"otomobil\", \"de\": \"autos\"}}', true, 0, NOW(), NOW(), '{cat_id}', 0, true, false, true, true, '[]', 0)"))
        
        # 3. Create Listings (TR and DE)
        user_id = str(uuid.uuid4())
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_code, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{user_id}', 'multi_country_user@test.com', 'hash', 'Global User', 'individual', true, true, 'TR', '[]', 'en', false, NOW(), NOW())"))
        
        # TR Listing
        await session.execute(text(f"INSERT INTO listings (id, title, user_id, category_id, status, price, currency, country, city, module, view_count, created_at, updated_at, is_dealer_listing, is_showcase, is_premium, images, attributes, image_count) VALUES (gen_random_uuid(), 'Istanbul Car', '{user_id}', '{cat_id}', 'active', 500000, 'TRY', 'TR', 'Istanbul', 'vehicle', 10, NOW(), NOW(), false, false, false, '[]', '{{}}', 0)"))
        
        # DE Listing
        await session.execute(text(f"INSERT INTO listings (id, title, user_id, category_id, status, price, currency, country, city, module, view_count, created_at, updated_at, is_dealer_listing, is_showcase, is_premium, images, attributes, image_count) VALUES (gen_random_uuid(), 'Berlin Auto', '{user_id}', '{cat_id}', 'active', 20000, 'EUR', 'DE', 'Berlin', 'vehicle', 5, NOW(), NOW(), false, false, false, '[]', '{{}}', 0)"))
        
        await session.commit()
        print("✅ Data Seeded")

if __name__ == "__main__":
    asyncio.run(seed_multi_country_data())
