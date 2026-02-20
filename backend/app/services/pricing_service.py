
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from sqlalchemy.exc import IntegrityError
from app.models.pricing import PriceConfig, FreeQuotaConfig, ListingConsumptionLog, Discount
from app.models.campaign import Campaign
from app.models.commercial import DealerSubscription
from app.models.billing import VatRate, InvoiceItem
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import uuid
from typing import Optional

class PricingException(Exception):
    """Base exception for pricing errors"""
    pass

class PricingConfigError(PricingException):
    """Configuration missing or invalid"""
    pass

class PricingConcurrencyError(PricingException):
    """Race condition or locked resource"""
    pass

class PricingIdempotencyError(PricingException):
    """Operation already performed"""
    pass

class CalculationResult:
    def __init__(self):
        self.is_free = False
        self.is_covered_by_package = False
        self.charge_amount = Decimal("0.00")
        self.currency = "EUR"
        self.source = "" # free_quota, subscription_quota, paid_extra
        self.vat_rate = Decimal("0.00")
        self.gross_amount = Decimal("0.00")
        self.price_config_id: Optional[uuid.UUID] = None
        self.price_config_version: Optional[int] = None
        self.applied_discount = Decimal("0.00")
        self.base_unit_price = Decimal("0.00")
        
    def to_dict(self):
        return {
            "is_free": self.is_free,
            "source": self.source,
            "charge_amount": float(self.charge_amount),
            "currency": self.currency,
            "gross_amount": float(self.gross_amount)
        }

class PricingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_idempotency(self, listing_id: str):
        """Ensures listing hasn't been consumed yet"""
        query = select(ListingConsumptionLog).where(
            ListingConsumptionLog.listing_id == uuid.UUID(listing_id)
        )
        existing = (await self.db.execute(query)).scalar_one_or_none()
        if existing:
            raise PricingIdempotencyError(f"Listing {listing_id} already consumed via {existing.consumed_source}")

    async def get_active_vat(self, country: str) -> VatRate:
        """Fetches active VAT rate or raises error"""
        query = select(VatRate).where(and_(
            VatRate.country == country,
            VatRate.is_active == True
        )).order_by(VatRate.valid_from.desc())
        
        vat = (await self.db.execute(query)).scalars().first()
        if not vat:
            raise PricingConfigError(f"No active VAT configuration found for country {country}")
        return vat

    async def calculate_listing_fee(self, dealer_id: str, country: str, listing_id: str, pricing_type: str = "pay_per_listing") -> CalculationResult:
        """
        Determines the cost of publishing a listing based on Waterfall Logic:
        1. Free Quota (Rolling Window)
        2. Subscription Quota (Active Package)
        3. Overage (Pay-per-listing)
        """
        # 0. Idempotency Check
        await self.check_idempotency(listing_id)

        # 0. Pre-flight Checks (VAT must exist)
        vat_config = await self.get_active_vat(country)
        
        result = CalculationResult()
        result.vat_rate = vat_config.rate
        now = datetime.now(timezone.utc)
        
        # === WATERFALL STEP 1: FREE QUOTA ===
        free_query = select(FreeQuotaConfig).where(and_(
            FreeQuotaConfig.country == country,
            FreeQuotaConfig.segment == "dealer", 
            FreeQuotaConfig.is_active == True
        ))
        free_config = (await self.db.execute(free_query)).scalar_one_or_none()
        
        if free_config:
            # Check usage in rolling window
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
                result.currency = "EUR" # Default fallback, normally derived from country map
                result.charge_amount = Decimal("0.00")
                result.gross_amount = Decimal("0.00")
                return result

        # === WATERFALL STEP 2: SUBSCRIPTION QUOTA ===
        # Check for active subscription with remaining quota
        sub_query = select(DealerSubscription).where(and_(
            DealerSubscription.dealer_id == uuid.UUID(dealer_id),
            DealerSubscription.status == "active",
            DealerSubscription.end_at > now
        ))
        # We don't lock here yet, just check availability
        subscriptions = (await self.db.execute(sub_query)).scalars().all()
        
        valid_sub = None
        for sub in subscriptions:
            remaining = sub.included_listing_quota - sub.used_listing_quota
            if remaining > 0:
                valid_sub = sub
                break
        
        if valid_sub:
            result.is_covered_by_package = True
            result.source = "subscription_quota"
            result.currency = "EUR" # Should come from package/sub
            result.charge_amount = Decimal("0.00")
            result.gross_amount = Decimal("0.00")
            return result

        # === WATERFALL STEP 3: OVERAGE (PAY-PER-LISTING) ===
        price_query = select(PriceConfig).where(and_(
            PriceConfig.country == country,
            PriceConfig.segment == "dealer",
            PriceConfig.pricing_type == pricing_type,
            PriceConfig.is_active == True
        ))
        price_config = (await self.db.execute(price_query)).scalar_one_or_none()
        
        if not price_config:
            raise PricingConfigError(f"No active price configuration found for {country}/dealer/{pricing_type}")

        # Populate Result
        result.is_free = False
        result.source = "paid_extra"
        result.price_config_id = price_config.id
        result.price_config_version = price_config.price_version
        result.currency = price_config.currency
        result.base_unit_price = price_config.unit_price_net
        result.charge_amount = price_config.unit_price_net
        
        # Calculate Tax
        tax_amount = result.charge_amount * (result.vat_rate / Decimal("100.00"))
        result.gross_amount = result.charge_amount + tax_amount

        result = await self.apply_campaign_discount(result, dealer_id, country, now)

        return result

    async def apply_campaign_discount(
        self,
        result: CalculationResult,
        dealer_id: str,
        country: str,
        now: datetime,
    ) -> CalculationResult:
        """Applies active campaign discount (read-path, safe no-op when DB not ready)."""
        try:
            query = select(Campaign).where(
                and_(
                    Campaign.type == "corporate",
                    Campaign.status == "active",
                    Campaign.start_at <= now,
                    Campaign.end_at >= now,
                    or_(
                        Campaign.country_scope == "global",
                        and_(Campaign.country_scope == "country", Campaign.country_code == country),
                    ),
                )
            ).order_by(desc(Campaign.priority), desc(Campaign.updated_at))

            campaign = (await self.db.execute(query)).scalars().first()
            if not campaign:
                return result

            if campaign.target != "discount":
                return result

            discount_value = None
            if campaign.discount_percent is not None:
                discount_value = (
                    result.charge_amount
                    * Decimal(str(campaign.discount_percent))
                    / Decimal("100.00")
                )
            elif campaign.discount_amount is not None:
                if campaign.discount_currency and campaign.discount_currency != result.currency:
                    return result
                discount_value = Decimal(str(campaign.discount_amount))

            if discount_value and discount_value > Decimal("0.00"):
                result.applied_discount = discount_value
                result.charge_amount = max(Decimal("0.00"), result.charge_amount - discount_value)
                tax_amount = result.charge_amount * (result.vat_rate / Decimal("100.00"))
                result.gross_amount = result.charge_amount + tax_amount

            return result
        except Exception:
            return result

    async def commit_usage(self, calculation: CalculationResult, listing_id: str, dealer_id: str, user_id: str, invoice_id: Optional[str] = None):
        """
        Atomically commits the usage:
        1. Re-validates locks (for subscriptions)
        2. Creates Consumption Log
        3. Creates InvoiceItem (if paid)
        4. Decrements Quota (if sub)
        """
        # 1. Idempotency Re-check
        await self.check_idempotency(listing_id)
        
        # 2. Handle Subscription Locking
        if calculation.source == "subscription_quota":
            # Must lock the subscription row to prevent race conditions
            sub_query = select(DealerSubscription).where(and_(
                DealerSubscription.dealer_id == uuid.UUID(dealer_id),
                DealerSubscription.status == "active",
                DealerSubscription.end_at > datetime.now(timezone.utc)
            )).with_for_update() # LOCK
            
            result = await self.db.execute(sub_query)
            # Find the one with quota
            subscriptions = result.scalars().all()
            valid_sub = None
            for sub in subscriptions:
                if (sub.included_listing_quota - sub.used_listing_quota) > 0:
                    valid_sub = sub
                    break
            
            if not valid_sub:
                # Fallback: Race condition hit, quota is gone.
                # Must abort or switch to paid. For strictness, we abort.
                raise PricingConcurrencyError("Subscription quota exhausted during transaction")
            
            # Deduct
            valid_sub.used_listing_quota += 1
            # Note: No need to save explicitly, SQLAlchemy tracks it.

        # 3. Create InvoiceItem if Paid
        invoice_item_id = None
        if calculation.source == "paid_extra":
            if not invoice_id:
                 # In a real app, we might create a draft invoice here.
                 # For now, we assume invoice_id is provided for paid transactions or we skip linking.
                 # But strictly, we need to snapshot values.
                 pass
            
            if invoice_id:
                inv_item = InvoiceItem(
                    invoice_id=uuid.UUID(invoice_id),
                    item_type="listing_fee",
                    description={"en": f"Listing Fee {listing_id}"},
                    quantity=1,
                    price_source=calculation.source,
                    base_unit_price=calculation.base_unit_price,
                    applied_vat_rate=calculation.vat_rate,
                    currency=calculation.currency,
                    country="DE", # Should be passed or derived
                    price_config_version=calculation.price_config_version,
                    unit_price_net=calculation.charge_amount,
                    line_net=calculation.charge_amount,
                    line_tax=calculation.gross_amount - calculation.charge_amount,
                    line_gross=calculation.gross_amount
                )
                self.db.add(inv_item)
                await self.db.flush() # Get ID
                invoice_item_id = inv_item.id

        # 4. Create Log
        log = ListingConsumptionLog(
            listing_id=uuid.UUID(listing_id),
            dealer_id=uuid.UUID(dealer_id) if dealer_id else None,
            user_id=uuid.UUID(user_id),
            consumed_source=calculation.source,
            price_config_id=calculation.price_config_id,
            invoice_item_id=invoice_item_id,
            charged_amount=calculation.charge_amount,
            currency=calculation.currency
        )
        self.db.add(log)
        
        # Commit handled by caller or here? 
        # Service methods should usually flush/commit if they own the transaction.
        # Since we use locking, we must be inside a transaction.
        try:
            await self.db.commit()
        except IntegrityError as e:
            await self.db.rollback()
            if "ix_consumption_logs" in str(e) or "listing_id" in str(e):
                 raise PricingIdempotencyError("Concurrent consumption detected")
            raise e
