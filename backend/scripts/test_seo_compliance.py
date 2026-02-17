
import asyncio
import os
import sys
import uuid
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.user import User
from app.models.vehicle_mdm import VehicleMake, VehicleModel

async def test_seo_compliance():
    print("🚀 Starting SEO Compliance Test...")
    
    # 1. Setup Data (1 Active, 1 Expired)
    active_id = uuid.uuid4()
    expired_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as session:
        # Get a user
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = res.scalar()
        if not user_id:
            print("❌ No users found. Seed DB first.")
            return

        # Active Listing
        active = Listing(
            id=active_id,
            title="SEO Active Listing",
            user_id=user_id,
            status="active",
            price=100, currency="EUR", country="DE", module="vehicle"
        )
        session.add(active)
        
        # Expired Listing
        expired = Listing(
            id=expired_id,
            title="SEO Expired Listing",
            user_id=user_id,
            status="expired",
            price=100, currency="EUR", country="DE", module="vehicle"
        )
        session.add(expired)
        
        await session.commit()
        print(f"✅ Created listings: Active({active_id}), Expired({expired_id})")

    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient() as client:
        # 2. Check Robots.txt
        print("\n🔹 Checking robots.txt...")
        resp = await client.get(f"{base_url}/robots.txt")
        if resp.status_code == 200:
            content = resp.text
            if "Disallow: /admin/" in content and "Sitemap:" in content:
                print("✅ robots.txt valid")
            else:
                print(f"❌ robots.txt invalid content: {content}")
        else:
            print(f"❌ robots.txt failed: {resp.status_code}")

        # 3. Check Sitemap Index
        print("\n🔹 Checking sitemap.xml...")
        resp = await client.get(f"{base_url}/sitemap.xml")
        if resp.status_code == 200 and "<sitemapindex" in resp.text:
            print("✅ sitemap.xml index valid")
        else:
            print(f"❌ sitemap.xml failed")

        # 4. Check Listings Sitemap (The Core Test)
        print("\n🔹 Checking listings sitemap (Active vs Expired)...")
        resp = await client.get(f"{base_url}/sitemaps/listings.xml")
        if resp.status_code == 200:
            xml = resp.text
            
            # Check Active
            if str(active_id) in xml:
                print("✅ Active listing found in sitemap")
            else:
                print(f"❌ Active listing MISSING from sitemap!")
                
            # Check Expired
            if str(expired_id) in xml:
                print(f"❌ Expired listing FOUND in sitemap! (SEO Fail)")
            else:
                print("✅ Expired listing correctly excluded")
        else:
            print(f"❌ Listings sitemap failed: {resp.status_code}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM listings WHERE id IN ('{active_id}', '{expired_id}')"))
        await session.commit()

    print("\n🎉 SEO Compliance Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_seo_compliance())
