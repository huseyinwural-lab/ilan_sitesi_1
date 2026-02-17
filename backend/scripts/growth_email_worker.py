import asyncio
import sys
import os
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.user import User

async def send_draft_reminders():
    print("📧 Checking for Abandoned Drafts...")
    
    async with AsyncSessionLocal() as db:
        # 1. Find Drafts older than 24h
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        query = select(Listing).where(
            Listing.status == 'draft',
            Listing.updated_at < cutoff,
            # Ideally verify user hasn't published it as another ID, but simple check for now
        )
        
        result = await db.execute(query)
        drafts = result.scalars().all()
        
        print(f"Found {len(drafts)} stale drafts.")
        
        for draft in drafts:
            user = await db.get(User, draft.user_id)
            if user:
                # Mock Send Email
                print(f"📨 SENDING EMAIL to {user.email}: 'Finish your listing: {draft.title}'")
                # In prod: Call EmailService
                
                # Mark as 'reminded' to avoid spamming? 
                # Need metadata column or separate log table. 
                # For MVP script, we just log.

if __name__ == "__main__":
    asyncio.run(send_draft_reminders())
