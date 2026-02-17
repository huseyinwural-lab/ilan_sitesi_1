
import logging
import random
import string
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User
from app.models.referral import ReferralReward
from app.models.billing import BillingCustomer
from fastapi import HTTPException
from app.services.referral_tier_service import ReferralTierService
import stripe
import os

logger = logging.getLogger(__name__)

class ReferralService:
    def __init__(self, db: AsyncSession):
        self.db = db
        stripe.api_key = os.environ.get("STRIPE_API_KEY")

    def generate_code(self, length=8) -> str:
        """Generates a random alphanumeric code"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))

    async def get_unique_referral_code(self) -> str:
        """Generates a guaranteed unique referral code"""
        for _ in range(5): # Retry limit
            code = self.generate_code()
            # Check existence
            res = await self.db.execute(select(User).where(User.referral_code == code))
            if not res.scalar_one_or_none():
                return code
        raise HTTPException(status_code=500, detail="Could not generate unique referral code")

    async def validate_referral_code(self, code: str) -> User:
        """Validates referral code and returns the referrer user"""
        if not code:
            return None
            
        res = await self.db.execute(select(User).where(User.referral_code == code))
        referrer = res.scalar_one_or_none()
        
        if not referrer:
            raise HTTPException(status_code=400, detail="Invalid referral code")
            
        return referrer

    async def process_reward(self, user_id: str, amount: float = None):
        """
        Processes reward for the referrer of the given user.
        Called on first successful payment.
        """
        # 1. Check if user has a referrer
        user_res = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = user_res.scalar_one_or_none()
        
        if not user or not user.referred_by:
            return # No referrer, nothing to do
            
        referrer_id = user.referred_by
        
        # 2. Check if reward already given
        # We assume one reward per referee.
        existing_reward = await self.db.execute(select(ReferralReward).where(ReferralReward.referee_id == user.id))
        if existing_reward.scalar_one_or_none():
            logger.info(f"Referral reward already given for user {user_id}")
            return # Idempotency
            
        # P18: Determine Reward Amount from Tier
        # If amount is not passed (default), calculate it.
        reward_amount = amount
        if reward_amount is None:
            tier_service = ReferralTierService(self.db)
            current_tier = await tier_service.get_current_tier(str(referrer_id))
            reward_amount = float(current_tier.reward_amount)
            
        # 3. Apply Reward to Referrer (Stripe Credit)
        # Fetch Referrer Billing Customer
        bill_res = await self.db.execute(select(BillingCustomer).where(BillingCustomer.user_id == referrer_id))
        referrer_billing = bill_res.scalar_one_or_none()
        
        status = "pending" # P16: Starts as pending, maturity job confirms later
        # Note: P16 changed logic to 'pending' -> 'confirmed'.
        # We do NOT apply Stripe Credit immediately in P16+ architecture.
        # We wait for maturity.
        # So we skip Stripe call here.
        
        # 4. Log Reward
        reward = ReferralReward(
            referrer_id=referrer_id,
            referee_id=user.id,
            amount=reward_amount,
            currency="TRY",
            status=status
        )
        self.db.add(reward)
        await self.db.commit() # Commit to get ID
        
        # P18: Check for Tier Upgrade
        # Although status is pending, some systems count pending referrals?
        # Policy P18 says "Confirmed referral count".
        # So we do NOT upgrade tier yet. Upgrade happens when status becomes 'confirmed'.
        # This will be handled by the maturity job or manual confirmation.
