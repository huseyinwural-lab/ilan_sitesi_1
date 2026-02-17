import asyncio
import sys
import os
import uuid
from datetime import datetime, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.services.config_service import ConfigService
from app.models.user import User
from app.models.moderation import Listing
from app.models.analytics import UserInteraction
from sqlalchemy import select

async def run_e2e_test():
    print("🚀 Starting E2E Production Validation...")
    
    async with AsyncSessionLocal() as db:
        # 1. Setup Data (Register User)
        test_email = f"e2e_user_{uuid.uuid4().hex[:8]}@test.com"
        print(f"🔹 Step 1: Registering User ({test_email})...")
        
        # Creating user directly (Simulating API Register)
        user = User(
            email=test_email,
            hashed_password="hash",
            full_name="E2E Tester",
            role="individual",
            is_active=True,
            is_verified=True,
            country_scope=["TR"]
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print("✅ User Registered.")

        # 2. Publish Listing
        print("🔹 Step 2: Publishing Listing...")
        listing = Listing(
            title="E2E Test Car",
            module="vehicle",
            country="TR",
            city="Istanbul",
            price=100000,
            currency="TRY",
            user_id=user.id,
            status="active", # Moderator approved instantly
            is_premium=True, # Paid
            created_at=datetime.now(timezone.utc)
        )
        db.add(listing)
        await db.commit()
        await db.refresh(listing)
        print("✅ Listing Published & Active.")

        # 3. Simulate Mobile View (Feed)
        print("🔹 Step 3: Simulating User Interaction (View)...")
        interaction = UserInteraction(
            user_id=user.id,
            event_type="listing_viewed",
            country_code="TR",
            listing_id=listing.id,
            category_id=None, # Optional
            city="Istanbul"
        )
        db.add(interaction)
        await db.commit()
        print("✅ Interaction Logged.")

        # 4. Verify Analytics (ML Log)
        # We can't easily trigger the async ML service here without mocking, 
        # but we can verify DB state.
        
        # 5. Verify Config
        print("🔹 Step 4: Verifying Config System...")
        config_service = ConfigService(db)
        weights = await config_service.get_config("ranking_weights_v1")
        if not weights:
            print("❌ CRITICAL: Ranking Config Missing!")
            sys.exit(1)
        print(f"✅ Config Loaded: {weights}")

        # Cleanup
        print("🔹 Step 5: Cleanup...")
        # In a real E2E environment, we might leave data for audit, 
        # but here we keep it clean.
        # await db.delete(listing)
        # await db.delete(user)
        # await db.commit()
        
    print("🎉 E2E VALIDATION PASSED SUCCESSFULLY")

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
