
import asyncio
import os
import sys
import uuid
from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.vehicle_mdm import VehicleMake, VehicleModel
from app.services.quota_service import QuotaService
from app.models.monetization import QuotaUsage
from app.models.category import Category

async def test_expiration_flow():
    print("🚀 Starting Expiration Flow Test...")
    
    # 1. Setup User & Create Expired Listing
    async with AsyncSessionLocal() as session:
        # Enable commit
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id_res = res.scalar()
        if not user_id_res:
            print("❌ No users found. Run seed script.")
            return
        user_id = str(user_id_res)
        
        # Get a valid Category
        cat_res = await session.execute(select(Category).limit(1))
        category = cat_res.scalar_one_or_none()
        if not category:
            print("❌ No categories found. Run seed first.")
            return
        category_id = category.id

        # Cleanup
        await session.execute(text(f"DELETE FROM quota_usage WHERE user_id = '{user_id}'"))
        await session.execute(text(f"DELETE FROM listings WHERE user_id = '{user_id}' AND title = 'Test Expire'"))
        await session.commit()
    
    async with AsyncSessionLocal() as session:
        try:
            # Create Listing
            now = datetime.now(timezone.utc)
            listing = Listing(
                title="Test Expire",
                user_id=uuid.UUID(user_id),
                status="active",
                created_at=now - timedelta(days=91),
                expires_at=now - timedelta(days=1),
                price=100, currency="TRY", country="TR", module="vehicle", category_id=category_id
            )
            session.add(listing)
            await session.commit()
        except Exception as e:
            print(f"❌ Error creating listing: {e}")
            raise e
        
    async with AsyncSessionLocal() as session:
        # Consume Quota
        qs = QuotaService(session)
        # Use simple update to avoid service transaction complexity in test script
        # Service uses with_for_update inside which needs transaction.
        # But here we are simulating usage.
        await session.execute(text(f"INSERT INTO quota_usage (id, user_id, resource, used, updated_at) VALUES ('{uuid.uuid4()}', '{user_id}', 'listing_active', 1, NOW())"))
        await session.commit()
        
        usage_before = await qs.get_usage(user_id, "listing_active")
        print(f"Usage Before: {usage_before}")

    # 2. Run Job Logic (New Session)
    print("Running Job Logic...")
    from scripts.process_expirations import process_expirations
    await process_expirations()
    
    # 3. Verify (New Session)
    async with AsyncSessionLocal() as session:
        qs = QuotaService(session)
        usage_after = await qs.get_usage(user_id, "listing_active")
        
        res = await session.execute(select(Listing).where(Listing.title == "Test Expire"))
        listing = res.scalar_one_or_none()
        
        print(f"Usage After: {usage_after}")
        print(f"Listing Status: {listing.status if listing else 'None'}")
        
        if listing and listing.status == 'expired' and usage_after == 0:
            print("✅ Expiration Successful (Status Changed & Quota Released)")
        else:
            print("❌ Expiration Failed")

if __name__ == "__main__":
    asyncio.run(test_expiration_flow())
