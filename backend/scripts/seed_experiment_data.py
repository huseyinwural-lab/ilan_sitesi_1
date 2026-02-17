import asyncio
import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.experimentation import ExperimentLog
from app.models.analytics import UserInteraction
from app.models.moderation import Listing

async def seed_experiment_data():
    print("🧪 Seeding Experiment Data (Group A vs B)...")
    
    async with AsyncSessionLocal() as db:
        # Create Dummy Listings if none
        listings = []
        for i in range(5):
            lid = uuid.uuid4()
            listings.append(lid)
            # We assume listings exist or we just use IDs for interactions (FK might fail if enforced, so let's check)
            # For speed, we'll fetch existing listings
            res = await db.execute(select(Listing.id).limit(10))
            existing = res.scalars().all()
            if existing:
                listings = existing
                break
        
        if not listings:
            print("❌ No listings found. Run seed_default_data first.")
            return

        # Simulate 100 Users
        for i in range(100):
            user_id = uuid.uuid4()
            
            # Assign Group (50/50)
            group = "A" if i % 2 == 0 else "B"
            
            # Log Exposure
            exp_log = ExperimentLog(
                user_id=user_id,
                experiment_name="revenue_boost_v1",
                variant=group,
                device_type="mobile",
                created_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 24))
            )
            db.add(exp_log)
            
            # Simulate Behavior
            # Group B (Treatment - Revenue Boost) has higher conversion assumed
            conversion_rate = 0.05 if group == "A" else 0.08
            
            # Views
            for _ in range(random.randint(3, 10)):
                db.add(UserInteraction(
                    user_id=user_id,
                    event_type="listing_viewed",
                    country_code="TR",
                    listing_id=random.choice(listings),
                    created_at=datetime.now(timezone.utc)
                ))
                
            # Conversion (Contact)
            if random.random() < conversion_rate:
                db.add(UserInteraction(
                    user_id=user_id,
                    event_type="listing_contact_clicked",
                    country_code="TR",
                    listing_id=random.choice(listings),
                    created_at=datetime.now(timezone.utc)
                ))

        await db.commit()
        print("✅ Seeded 100 users with experiment data.")

if __name__ == "__main__":
    asyncio.run(seed_experiment_data())
