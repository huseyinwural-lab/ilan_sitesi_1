
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.pricing import PriceConfig, FreeQuotaConfig, ListingConsumptionLog, Discount
from app.models.commercial import DealerSubscription
from app.models.billing import VatRate
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid

class CalculationResult:
    def __init__(self):
        self.is_free = False
        self.is_covered_by_package = False
        self.charge_amount = Decimal("0.00")
        self.currency = "EUR"
        self.source = "" # free_quota, subscription_quota, paid_extra
        self.vat_rate = Decimal("0.00")
        self.gross_amount = Decimal("0.00")
        self.price_config_id = None
        self.applied_discount = Decimal("0.00")

class PricingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_listing_fee(self, dealer_id: str, country: str, user_id: str) -> CalculationResult:
        result = CalculationResult()
        now = datetime.now(timezone.utc)
        
        # 1. Check Free Quota (Rolling Window)
        # Get config
        free_config_res = await self.db.execute(select(FreeQuotaConfig).where(and_(
            FreeQuotaConfig.country == country,
            FreeQuotaConfig.segment == "dealer", # Assuming dealer flow for now
            FreeQuotaConfig.is_active == True
        )))
        free_config = free_config_res.scalar_one_or_none()
        
        if free_config:
            # Count usage in window
            window_start = now - timedelta(days=free_config.period_days)
            usage_query = select(func.count(ListingConsumptionLog.id)).where(and_(
                ListingConsumptionLog.dealer_id == uuid.UUID(dealer_id),
                ListingConsumptionLog.consumed_source == "free_quota",
                ListingConsumptionLog.created_at >= window_start
            ))
            usage_count = (await self.db.execute(usage_query)).scalar() or 0
            
            if usage_count < free_config.quota_amount:
                result.is_free = True
                result.source = "free_quota"
                result.currency = "EUR" # Default fallback
                return result

        # 2. Check Subscription Quota
        # Get Active Subscription
        sub_res = await self.db.execute(select(DealerSubscription).where(and_(
            DealerSubscription.dealer_id == uuid.UUID(dealer_id),
            DealerSubscription.status == "active",
            DealerSubscription.end_at > now
        )))
        subscription = sub_res.scalar_one_or_none()
        
        if subscription:
            # Check remaining
            # Logic: included - used > 0
            remaining = subscription.included_listing_quota - subscription.used_listing_quota
            if remaining > 0:
                result.is_covered_by_package = True
                result.source = "subscription_quota"
                result.currency = "EUR" # Default fallback or sub currency
                return result

        # 3. Pay-Per-Listing (Waterfall End)
        # Get Price Config
        price_res = await self.db.execute(select(PriceConfig).where(and_(
            PriceConfig.country == country,
            PriceConfig.segment == "dealer",
            PriceConfig.pricing_type == "pay_per_listing",
            PriceConfig.is_active == True
        )))
        price_config = price_res.scalar_one_or_none()
        
        if not price_config:
            # No price defined -> Block action? Or zero? 
            # Safe default: Block/Error. But here we return "Charge" with 0 or raise.
            # Let's assume configuration MUST exist.
            # Raising exception in service layer might be okay or return error state.
            raise ValueError(f"No pricing configuration found for {country} dealer listing")
            
        result.charge_amount = price_config.unit_price_net
        result.currency = price_config.currency
        result.source = "paid_extra"
        result.price_config_id = price_config.id
        
        # 4. Apply Discounts (Simple: Fixed or Percentage)
        # Fetch applicable discounts
        # discount_res = ... (Skipping for MVP simplicity as per "Discount Stacking Kapalı")
        # Assuming no discount for now.
        
        # 5. Calculate VAT
        vat_res = await self.db.execute(select(VatRate).where(and_(
            VatRate.country == country,
            VatRate.is_active == True
        )).order_by(VatRate.valid_from.desc()))
        vat_config = vat_res.scalars().first()
        
        vat_rate = vat_config.rate if vat_config else Decimal("0.00")
        result.vat_rate = vat_rate
        
        tax_amount = result.charge_amount * (vat_rate / 100)
        result.gross_amount = result.charge_amount + tax_amount
        
        return result

    async def commit_usage(self, calculation: CalculationResult, listing_id: str, dealer_id: str, user_id: str, invoice_item_id: str = None):
        """Records the consumption log"""
        log = ListingConsumptionLog(
            listing_id=uuid.UUID(listing_id),
            dealer_id=uuid.UUID(dealer_id) if dealer_id else None,
            user_id=uuid.UUID(user_id),
            consumed_source=calculation.source,
            price_config_id=calculation.price_config_id,
            invoice_item_id=uuid.UUID(invoice_item_id) if invoice_item_id else None,
            charged_amount=calculation.charge_amount,
            currency=calculation.currency
        )
        self.db.add(log)
        
        # If subscription used, increment usage
        if calculation.source == "subscription_quota":
             # Lock row
             sub_res = await self.db.execute(select(DealerSubscription).where(and_(
                DealerSubscription.dealer_id == uuid.UUID(dealer_id),
                DealerSubscription.status == "active"
             )).with_for_update())
             sub = sub_res.scalar_one_or_none()
             if sub:
                 sub.used_listing_quota += 1
        
        await self.db.commit()
