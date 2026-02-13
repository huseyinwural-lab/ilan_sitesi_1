
import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.moderation import Listing

async def cleanup_null_make_listings():
    print("🧹 Cleaning up Listings with NULL Make/Model...")
    
    async with AsyncSessionLocal() as session:
        # Fetch them
        res = await session.execute(select(Listing).where(
            Listing.module == 'vehicle',
            (Listing.make_id == None) | (Listing.model_id == None)
        ))
        listings = res.scalars().all()
        
        if not listings:
            print("✅ No listings to clean.")
            return

        print(f"Found {len(listings)} listings to delete.")
        for l in listings:
            print(f"   -> Deleting {l.title} (ID: {l.id})")
            await session.delete(l)
        
        await session.commit()
        print("🎉 Cleanup Complete.")

if __name__ == "__main__":
    asyncio.run(cleanup_null_make_listings())
