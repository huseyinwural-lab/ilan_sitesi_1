
import asyncio
import os
import sys
from sqlalchemy import text, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.services.quota_service import QuotaService

async def process_expirations():
    print("⏰ Starting Expiration Job...")
    
    async with AsyncSessionLocal() as session:
        quota_service = QuotaService(session)
        now = datetime.now(timezone.utc)
        
        # 1. Find Expired Listings
        stmt = select(Listing).where(
            Listing.status == 'active',
            Listing.expires_at < now
        ).limit(1000) # Batch size
        
        res = await session.execute(stmt)
        expired_listings = res.scalars().all()
        
        if not expired_listings:
            print("✅ No listings to expire.")
            return

        print(f"📉 Expiring {len(expired_listings)} listings...")
        
        processed = 0
        for listing in expired_listings:
            try:
                # Transaction per listing or batch?
                # Per listing is safer for quota integrity logic if complex.
                # Batch is faster. Given P13 scope, let's do batch but handle quota carefully.
                # Actually, quota service release needs lock.
                
                async with session.begin_nested(): # Savepoint
                    # 1. Update Status
                    listing.status = 'expired'
                    listing.updated_at = now
                    
                    # 2. Release Quota
                    # We need user_id. Listing object has it.
                    await quota_service.release_quota(str(listing.user_id), "listing_active", 1)
                    
                    if listing.is_showcase:
                        await quota_service.release_quota(str(listing.user_id), "showcase_active", 1)
                        listing.is_showcase = False # Remove boost
                
                processed += 1
            except Exception as e:
                print(f"❌ Error expiring listing {listing.id}: {e}")
        
        await session.commit()
        print(f"✅ Processed {processed}/{len(expired_listings)} expirations.")

if __name__ == "__main__":
    asyncio.run(process_expirations())
