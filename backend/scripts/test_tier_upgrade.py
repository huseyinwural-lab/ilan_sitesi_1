
import asyncio
import os
import sys
import uuid
from decimal import Decimal
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.referral_tier import ReferralTier
from app.models.user import User
from app.services.referral_tier_service import ReferralTierService

async def seed_tiers_and_test():
    print("🚀 Seeding Tiers & Testing Upgrade...")
    
    async with AsyncSessionLocal() as session:
        # 1. Seed Tiers
        # Cleanup first
        await session.execute(text("DELETE FROM referral_tiers"))
        
        tiers = [
            {"name": "Standard", "min": 0, "reward": 100},
            {"name": "Gold", "min": 5, "reward": 150},
            {"name": "Platinum", "min": 20, "reward": 200},
        ]
        
        for t in tiers:
            tier = ReferralTier(
                id=uuid.uuid4(),
                name=t["name"],
                min_count=t["min"],
                reward_amount=Decimal(t["reward"]),
                currency="TRY",
                is_active=True
            )
            session.add(tier)
        
        await session.commit()
        print("✅ Tiers Seeded")
        
        # 2. Setup Test User
        user_id = str(uuid.uuid4())
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, referral_count_confirmed, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{user_id}', 'tier_test_{user_id[:8]}@test.com', 'hash', 'Tier Tester', 'individual', true, true, 4, '[]', 'en', false, NOW(), NOW())")) # Starts with 4
        await session.commit()
        
        # 3. Test Upgrade Logic
        service = ReferralTierService(session)
        
        # Current Tier (Should be None or implied Standard)
        # But user.referral_tier_id is null.
        
        # Action: Reward Confirmed (Count 4 -> 5)
        print("🔹 Triggering Upgrade (4 -> 5)...")
        await service.check_and_upgrade_tier(user_id)
        await session.commit()
        
        # Verify
        user_res = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = user_res.scalar_one()
        
        print(f"   Count: {user.referral_count_confirmed}")
        
        tier_res = await session.execute(select(ReferralTier).where(ReferralTier.id == user.referral_tier_id))
        tier = tier_res.scalar_one()
        print(f"   Tier: {tier.name}")
        
        if user.referral_count_confirmed == 5 and tier.name == "Gold":
            print("✅ Upgrade to Gold Successful")
        else:
            print("❌ Upgrade Failed")

if __name__ == "__main__":
    asyncio.run(seed_tiers_and_test())
