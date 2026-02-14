
import asyncio
import os
import sys
from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.services.quota_service import QuotaService
from app.models.monetization import QuotaUsage

async def test_expiration_flow():
    print("🚀 Starting Expiration Flow Test...")
    
    # Need TWO separate sessions to simulate Job behavior correctly without session state pollution
    
    # 1. Setup User & Create Expired Listing
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = str(res.scalar())
        
        # Cleanup
        await session.execute(text(f"DELETE FROM quota_usage WHERE user_id = '{user_id}'"))
        await session.execute(text(f"DELETE FROM listings WHERE user_id = '{user_id}' AND title = 'Test Expire'")) # Cleanup prev run
        
        # Create Listing
        now = datetime.now(timezone.utc)
        listing = Listing(
            title="Test Expire",
            user_id=uuid.UUID(user_id),
            status="active",
            created_at=now - timedelta(days=91),
            expires_at=now - timedelta(days=1),
            price=100, currency="TRY", country="TR", module="vehicle", category_id=uuid.UUID('dbf7def0-b233-4e49-8b00-75b4340685f3')
        )
        session.add(listing)
        
        # Consume Quota (Directly)
        qs = QuotaService(session)
        # We need explicit commit after consume to persist
        await qs.consume_quota(user_id, "listing_active", 1)
        
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

import uuid
if __name__ == "__main__":
    asyncio.run(test_expiration_flow())
