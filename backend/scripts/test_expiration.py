
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
    
    async with AsyncSessionLocal() as session:
        # 1. Setup User & Quota
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = str(res.scalar())
        qs = QuotaService(session)
        
        # Reset Quota
        await session.execute(text(f"DELETE FROM quota_usage WHERE user_id = '{user_id}'"))
        
        # 2. Create Expired Listing
        print("Creating expired listing...")
        now = datetime.now(timezone.utc)
        listing = Listing(
            title="Test Expire",
            user_id=uuid.UUID(user_id),
            status="active",
            created_at=now - timedelta(days=91),
            expires_at=now - timedelta(days=1), # Expired yesterday
            price=100, currency="TRY", country="TR", category_id=uuid.UUID('dbf7def0-b233-4e49-8b00-75b4340685f3') # Random cat
        )
        session.add(listing)
        
        # Manually consume quota
        await qs.consume_quota(user_id, "listing_active", 1)
        await session.commit()
        
        usage_before = await qs.get_usage(user_id, "listing_active")
        print(f"Usage Before: {usage_before}")
        if usage_before != 1:
            print("❌ Setup failed")
            return

        # 3. Run Job Logic
        print("Running Job Logic...")
        from scripts.process_expirations import process_expirations
        await process_expirations()
        
        # 4. Verify
        await session.refresh(listing)
        usage_after = await qs.get_usage(user_id, "listing_active")
        print(f"Usage After: {usage_after}")
        print(f"Listing Status: {listing.status}")
        
        if listing.status == 'expired' and usage_after == 0:
            print("✅ Expiration Successful (Status Changed & Quota Released)")
        else:
            print("❌ Expiration Failed")

import uuid
if __name__ == "__main__":
    asyncio.run(test_expiration_flow())
