
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.referral_tier import ReferralTier
from app.models.user import User
import uuid

logger = logging.getLogger(__name__)

class ReferralTierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_current_tier(self, user_id: str) -> ReferralTier:
        """Fetch current tier object for user"""
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        user = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not user or not user.referral_tier_id:
            # Fallback to Standard (Min Count 0)
            tier_stmt = select(ReferralTier).where(ReferralTier.min_count == 0)
            return (await self.db.execute(tier_stmt)).scalar_one()
            
        tier_stmt = select(ReferralTier).where(ReferralTier.id == user.referral_tier_id)
        return (await self.db.execute(tier_stmt)).scalar_one()

    async def check_and_upgrade_tier(self, user_id: str):
        """
        Called after a confirmed referral.
        Increments count and checks for tier upgrade.
        """
        user_uuid = uuid.UUID(user_id)
        
        # 1. Increment Count
        # We assume this method is called within a transaction of reward confirmation
        # But if separate, we should lock.
        # Simple update:
        await self.db.execute(
            update(User)
            .where(User.id == user_uuid)
            .values(referral_count_confirmed=User.referral_count_confirmed + 1)
        )
        # Flush to get new value if we need it, but we can just fetch it
        await self.db.flush()
        
        # Fetch updated user
        user = (await self.db.execute(select(User).where(User.id == user_uuid))).scalar_one()
        current_count = user.referral_count_confirmed
        
        # 2. Find Appropriate Tier
        # Get all tiers ordered by min_count desc
        tiers = (await self.db.execute(select(ReferralTier).order_by(ReferralTier.min_count.desc()))).scalars().all()
        
        target_tier = None
        for tier in tiers:
            if current_count >= tier.min_count:
                target_tier = tier
                break
        
        if not target_tier:
            return # Should not happen if Standard (0) exists
            
        # 3. Apply Upgrade if needed
        # We only upgrade, never downgrade (Policy P18.3.2)
        # Check current tier
        current_tier_id = user.referral_tier_id
        
        # If no tier assigned, or target is different (and strictly higher implied by logic if we don't downgrade)
        # Actually, we should check if target_tier > current_tier
        # But if we don't downgrade, we just check if target.min_count > current.min_count?
        # Or simply: if user.referral_tier_id != target_tier.id:
        # BUT wait, what if referral count dropped (e.g. manual correction)? We shouldn't downgrade.
        
        should_update = False
        if current_tier_id is None:
            should_update = True
        elif current_tier_id != target_tier.id:
            # Check if target is higher
            current_tier_obj = (await self.db.execute(select(ReferralTier).where(ReferralTier.id == current_tier_id))).scalar_one()
            if target_tier.min_count > current_tier_obj.min_count:
                should_update = True
        
        if should_update:
            user.referral_tier_id = target_tier.id
            self.db.add(user)
            logger.info(f"🚀 User {user_id} upgraded to {target_tier.name} Tier!")
            # Trigger Notification/Badge Event here if needed
