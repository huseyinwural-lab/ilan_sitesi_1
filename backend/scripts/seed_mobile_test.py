import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.user import User
from datetime import datetime, timezone

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def seed_active_listing():
    print("Seeding active listing for mobile test...")
    async with AsyncSessionLocal() as db:
        # Get admin user
        result = await db.execute(select(User).where(User.email == "admin@platform.com"))
        user = result.scalar_one_or_none()
        
        if user:
            listing = Listing(
                title="Mobile Test Car",
                description="Testing mobile feed",
                module="vehicle",
                country="DE",
                city="Berlin",
                price=50000,
                currency="EUR",
                user_id=user.id,
                status="active", # Crucial
                published_at=datetime.now(timezone.utc),
                images=["https://example.com/car.jpg"],
                is_premium=True
            )
            db.add(listing)
            await db.commit()
            print("Seeded active listing.")
        else:
            print("Admin user not found.")

if __name__ == "__main__":
    asyncio.run(seed_active_listing())
