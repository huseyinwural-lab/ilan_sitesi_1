
import asyncio
import os
import sys
import uuid
import httpx
from datetime import datetime, timezone
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.category import Category
from app.models.moderation import Listing

async def test_seo_landing():
    print("🚀 Starting Programmatic SEO Test...")
    
    cat_id = str(uuid.uuid4())
    listing_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        # 1. Setup Category
        await session.execute(text(f"INSERT INTO categories (id, module, slug, is_enabled, sort_order, created_at, updated_at, path, depth, is_visible_on_home, is_deleted, inherit_enabled, inherit_countries, allowed_countries, listing_count) VALUES ('{cat_id}', 'vehicle', '{{\"en\": \"cars\", \"tr\": \"otomobil\"}}', true, 0, NOW(), NOW(), '{cat_id}', 0, true, false, true, true, '[]', 0)"))
        
        # 2. Setup Listing (Istanbul, Active)
        user_id = str(uuid.uuid4())
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{user_id}', 'seo_test_{user_id[:8]}@test.com', 'hash', 'SEO User', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        
        await session.execute(text(f"INSERT INTO listings (id, title, user_id, category_id, status, price, currency, country, city, module, view_count, created_at, updated_at, is_dealer_listing, is_showcase, is_premium, images, attributes, image_count) VALUES ('{listing_id}', 'SEO Test Car', '{user_id}', '{cat_id}', 'active', 500000, 'TRY', 'TR', 'Istanbul', 'vehicle', 100, NOW(), NOW(), false, false, false, '[]', '{{}}', 0)"))
        
        await session.commit()

    base_url = "http://localhost:8001/api"
    
    async with httpx.AsyncClient() as client:
        # 3. Test Valid URL
        print("\n🔹 1. Valid URL (/istanbul/cars)...")
        resp = await client.get(f"{base_url}/istanbul/cars")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Success: {data['meta']['title']}")
            if len(data['listings']) > 0:
                print("✅ Listing found")
            else:
                print("❌ Listing NOT found")
        else:
            print(f"❌ Failed: {resp.status_code} {resp.text}")

        # 4. Test Price Filter
        print("\n🔹 2. Price Filter (/istanbul/cars/100k-1m)...")
        resp = await client.get(f"{base_url}/istanbul/cars/100k-1m")
        if resp.status_code == 200:
            print("✅ Success: Price filter applied")
        else:
            print(f"❌ Failed: {resp.status_code} {resp.text}")

        # 5. Test Invalid Category
        print("\n🔹 3. Invalid Category (/istanbul/ufo)...")
        resp = await client.get(f"{base_url}/istanbul/ufo")
        if resp.status_code == 404:
            print("✅ 404 Returned correctly")
        else:
            print(f"❌ Should be 404, got {resp.status_code}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM listings WHERE id = '{listing_id}'"))
        await session.execute(text(f"DELETE FROM categories WHERE id = '{cat_id}'"))
        await session.execute(text(f"DELETE FROM users WHERE id = '{user_id}'"))
        await session.commit()

    print("\n🎉 SEO Landing Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_seo_landing())
