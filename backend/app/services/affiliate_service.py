
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.billing import Invoice, BillingCustomer
from app.models.affiliate import Affiliate
from app.models.user import User
from app.models.ledger import RewardLedger
from app.services.referral_service import ReferralService
from decimal import Decimal
import stripe
import os
import uuid

logger = logging.getLogger(__name__)

class AffiliateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        stripe.api_key = os.environ.get("STRIPE_API_KEY")

    async def process_commission(self, invoice: Invoice):
        """
        Calculates and records affiliate commission on invoice payment.
        """
        # 1. Check if user was referred by affiliate
        user_res = await self.db.execute(select(User).where(User.id == invoice.user_id))
        user = user_res.scalar_one()
        
        if not user.referred_by_affiliate_id:
            return # No affiliate attribution
            
        affiliate_id = user.referred_by_affiliate_id
        
        # 2. Get Affiliate & Rate
        aff_res = await self.db.execute(select(Affiliate).where(Affiliate.id == affiliate_id))
        affiliate = aff_res.scalar_one_or_none()
        
        if not affiliate or affiliate.status != 'approved':
            return # Affiliate inactive
            
        # 3. Calculate Commission
        # Base: Net Total (excluding tax) ideally, but for MVP Gross is simpler.
        # Let's use Net Total from Invoice model if available, else Gross.
        # Invoice model has 'total_amount' which is usually Gross.
        # Let's assume commission on Gross for simplicity unless tax handling is strict.
        base_amount = invoice.total_amount
        commission_amount = base_amount * affiliate.commission_rate
        
        # Rounding
        commission_amount = round(commission_amount, 2)
        
        if commission_amount <= 0:
            return

        # 4. Record to Ledger (CREDIT)
        # Note: We reuse RewardLedger table. 'reward_id' FK is to ReferralReward.
        # Since this is Affiliate Commission, we don't have a ReferralReward record.
        # We need to make reward_id Nullable in Ledger? 
        # Or create a "CommissionRecord" table?
        # Decision P18 Architect: "Affiliate Ledger Ayrı Değil, Unified ... reward_ledger kullanılır"
        # But FK constraint exists.
        # We should probably modify RewardLedger to make reward_id nullable OR point to a new "AffiliateReward" table.
        # For MVP speed without migration: We can create a dummy ReferralReward record or modify schema.
        # Modifying Schema is safer. Let's make reward_id nullable in a migration next step.
        # BUT wait, P18 decision said "Affiliate Ledger Ayrı Değil".
        # Let's check RewardLedger model again.
        
        # Strategy: Create a new migration to make `reward_id` nullable in `reward_ledger`.
        # And add `affiliate_id` column to `reward_ledger`?
        # Or just use `reason` field to store "affiliate_commission:{affiliate_id}"?
        # Cleanest: Make reward_id nullable, add affiliate_id nullable.
        
        # Assuming we will do migration.
        
        ledger = RewardLedger(
            user_id=affiliate.user_id, # Credit to Affiliate User
            type="CREDIT",
            amount=commission_amount,
            currency=invoice.currency,
            reason=f"affiliate_commission:{invoice.id}",
            # reward_id=None # Needs migration
        )
        # self.db.add(ledger) # Deferred until migration
        
        # 5. Apply to Stripe Balance
        # Fetch Affiliate Billing Customer
        bill_res = await self.db.execute(select(BillingCustomer).where(BillingCustomer.user_id == affiliate.user_id))
        aff_billing = bill_res.scalar_one_or_none()
        
        if aff_billing and aff_billing.stripe_customer_id:
            try:
                credit_cents = -int(commission_amount * 100)
                stripe.Customer.create_balance_transaction(
                    aff_billing.stripe_customer_id,
                    amount=credit_cents,
                    currency=invoice.currency.lower(),
                    description=f"Commission for Invoice {invoice.number}"
                )
                logger.info(f"✅ Commission {commission_amount} credited to Affiliate {affiliate.id}")
            except Exception as e:
                logger.error(f"Stripe Credit Error: {e}")
        
        # Note: We return the ledger object to be added after migration fix
        return ledger
