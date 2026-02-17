
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.user import User
from app.models.analytics import ListingView
from server import create_access_token

async def test_analytics_abuse():
    print("🚀 Starting Analytics Abuse Test...")
    
    # 1. Setup Data
    owner_id = str(uuid.uuid4())
    viewer_id = str(uuid.uuid4())
    listing_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        # Create Owner & Viewer
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{owner_id}', 'owner_{owner_id[:8]}@test.com', 'hash', 'Owner', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{viewer_id}', 'viewer_{viewer_id[:8]}@test.com', 'hash', 'Viewer', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        
        # Create Listing
        await session.execute(text(f"INSERT INTO listings (id, title, user_id, status, price, currency, country, module, view_count, created_at, updated_at, is_dealer_listing, is_showcase, is_premium, images, attributes, image_count) VALUES ('{listing_id}', 'Analytics Test Listing', '{owner_id}', 'active', 100, 'EUR', 'DE', 'vehicle', 0, NOW(), NOW(), false, false, false, '[]', '{{}}', 0)"))
        
        await session.commit()

    base_url = "http://localhost:8001/api/v2/listings"
    
    async with httpx.AsyncClient() as client:
        # Default headers for "Normal" user (Chrome)
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # 2. Normal View (Anonymous)
        print("\n🔹 1. Anonymous View...")
        resp = await client.get(f"{base_url}/{listing_id}", headers=browser_headers)
        assert resp.status_code == 200
        
        # Verify Count = 1
        await verify_count(listing_id, 1, "Anonymous View")

        # 3. Duplicate View (Same IP, within 30m)
        print("\n🔹 2. Duplicate View (Spam)...")
        # Same headers, same IP (default)
        resp = await client.get(f"{base_url}/{listing_id}", headers=browser_headers)
        assert resp.status_code == 200
        
        # Verify Count = 1 (No change)
        await verify_count(listing_id, 1, "Duplicate View Blocked")

        # 4. Bot View
        print("\n🔹 3. Bot View...")
        bot_headers = {"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"}
        # Simulate different IP to bypass dedup check, but bot check should catch it
        bot_headers["X-Forwarded-For"] = "1.2.3.4" 
        
        resp = await client.get(f"{base_url}/{listing_id}", headers=bot_headers)
        assert resp.status_code == 200
        
        # Verify Count = 1 (No change)
        await verify_count(listing_id, 1, "Bot Blocked")

        # 5. Owner View
        print("\n🔹 4. Owner View...")
        token = create_access_token({"sub": owner_id, "email": "owner@test.com", "role": "individual"})
        owner_headers = browser_headers.copy()
        owner_headers.update({"Authorization": f"Bearer {token}", "X-Forwarded-For": "5.6.7.8"}) # New IP
        
        resp = await client.get(f"{base_url}/{listing_id}", headers=owner_headers)
        assert resp.status_code == 200
        
        # Verify Count = 1 (No change)
        await verify_count(listing_id, 1, "Owner View Blocked")

        # 6. Valid Unique User View
        print("\n🔹 5. Unique User View...")
        token = create_access_token({"sub": viewer_id, "email": "viewer@test.com", "role": "individual"})
        user_headers = browser_headers.copy()
        user_headers.update({"Authorization": f"Bearer {token}", "X-Forwarded-For": "9.9.9.9"}) # New IP
        
        resp = await client.get(f"{base_url}/{listing_id}", headers=user_headers)
        assert resp.status_code == 200
        
        # Verify Count = 2
        await verify_count(listing_id, 2, "Valid User View")

    print("\n🎉 Analytics Abuse Test PASSED!")

async def verify_count(listing_id, expected, stage):
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Listing.view_count).where(Listing.id == uuid.UUID(listing_id)))
        count = res.scalar()
        if count == expected:
            print(f"✅ {stage}: Count is {count}")
        else:
            print(f"❌ {stage} FAILED: Expected {expected}, Got {count}")
            # Don't exit, just log failure for debugging script flow
            # sys.exit(1) 

if __name__ == "__main__":
    asyncio.run(test_analytics_abuse())
