
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
from app.core.redis_cache import cache_service

async def process_expirations():
    print("⏰ Starting Expiration Job...")
    
    # Connect Redis
    await cache_service.connect()
    
    try:
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
                    async with session.begin_nested(): # Savepoint
                        # 1. Update Status
                        listing.status = 'expired'
                        listing.updated_at = now
                        
                        # 2. Release Quota
                        await quota_service.release_quota(str(listing.user_id), "listing_active", 1)
                        
                        if listing.is_showcase:
                            await quota_service.release_quota(str(listing.user_id), "showcase_active", 1)
                            listing.is_showcase = False # Remove boost
                    
                    processed += 1
                except Exception as e:
                    print(f"❌ Error expiring listing {listing.id}: {e}")
            
            await session.commit()
            print(f"✅ Processed {processed}/{len(expired_listings)} expirations.")
            
            # 3. Invalidate Cache
            if processed > 0:
                print("🧹 Cleaning Search Cache...")
                await cache_service.clear_by_pattern("search:v2:*")
                print("✅ Cache Cleared.")
                
    finally:
        await cache_service.close()

if __name__ == "__main__":
    asyncio.run(process_expirations())
