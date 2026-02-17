
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.promotion import Promotion, Coupon, CouponRedemption
from datetime import datetime, timezone
from fastapi import HTTPException
import stripe
import os

logger = logging.getLogger(__name__)

class PromotionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        stripe.api_key = os.environ.get("STRIPE_API_KEY")

    async def validate_coupon(self, code: str, user_id: str):
        """
        Validates coupon runtime rules.
        Returns (Coupon, Promotion) tuple if valid.
        Raises HTTPException if invalid.
        """
        code = code.strip().upper()
        
        # 1. Fetch Coupon & Promotion
        stmt = select(Coupon, Promotion).join(Promotion).where(Coupon.code == code)
        result = await self.db.execute(stmt)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail="Invalid coupon code")
            
        coupon, promo = row
        
        # 2. Basic Status Checks
        if not coupon.is_active or not promo.is_active:
            raise HTTPException(status_code=400, detail="Coupon is inactive")
            
        now = datetime.now(timezone.utc)
        if now < promo.start_at:
             raise HTTPException(status_code=400, detail="Promotion not started yet")
             
        if promo.end_at and now > promo.end_at:
             raise HTTPException(status_code=400, detail="Promotion expired")
             
        # 3. Global Limits (Promotion Level)
        if promo.max_redemptions:
            # Count total redemptions for this promo
            # Note: This is an approximation if not locked, but acceptable for read-heavy check
            count_stmt = select(func.count(CouponRedemption.id)).join(Coupon).where(Coupon.promotion_id == promo.id)
            total_used = (await self.db.execute(count_stmt)).scalar() or 0
            
            if total_used >= promo.max_redemptions:
                raise HTTPException(status_code=400, detail="Promotion limit reached")

        # 4. Coupon Limits (Code Level)
        if coupon.usage_limit:
            if coupon.usage_count >= coupon.usage_limit:
                raise HTTPException(status_code=400, detail="Coupon usage limit reached")
                
        # 5. User Limit
        user_usage_stmt = select(func.count(CouponRedemption.id)).where(
            and_(
                CouponRedemption.coupon_id == coupon.id,
                CouponRedemption.user_id == user_id
            )
        )
        user_used = (await self.db.execute(user_usage_stmt)).scalar() or 0
        
        if user_used >= coupon.per_user_limit:
             raise HTTPException(status_code=400, detail="You have already used this coupon")
             
        return coupon, promo

    async def get_or_create_stripe_coupon(self, promo: Promotion):
        """
        Syncs internal promotion to Stripe Coupon.
        Returns Stripe Coupon ID.
        """
        if promo.stripe_coupon_id:
            return promo.stripe_coupon_id
            
        # Create in Stripe
        try:
            duration = "once" # MVP Assumption: Discount applies once to the first invoice? 
            # Or "forever" for subscription? 
            # Let's assume "once" for simple discount on first payment, or "forever" if it's a recurring discount plan.
            # Usually simple coupons are "once" or "repeating" (x months).
            # For simplicity in MVP: "once" (First month discount).
            
            stripe_coupon = stripe.Coupon.create(
                name=promo.name,
                percent_off=float(promo.value) if promo.promo_type == 'percentage' else None,
                amount_off=int(promo.value * 100) if promo.promo_type == 'fixed_amount' else None,
                currency=promo.currency.lower() if promo.promo_type == 'fixed_amount' else None,
                duration="once" 
            )
            
            # Update DB
            promo.stripe_coupon_id = stripe_coupon.id
            # We need to commit this side-effect, but we might be in a read-only transaction from validate?
            # It's better to commit.
            self.db.add(promo)
            await self.db.commit()
            
            return stripe_coupon.id
            
        except Exception as e:
            logger.error(f"Stripe Coupon Create Error: {e}")
            # Fallback: Don't raise, try to proceed? No, payment will fail without ID.
            raise HTTPException(status_code=502, detail="External payment provider error (Coupon Sync)")

    async def apply_promotion(self, listing_id: str, product_key: str, admin_id: str = None):
        """
        P17: Applies a premium product to a listing.
        Handles logic for Showcase, Urgent, Bold, and Boost.
        """
        from app.models.moderation import Listing
        from app.models.premium import PremiumProduct, ListingPromotion
        
        # 1. Fetch Listing & Product
        listing_res = await self.db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
        listing = listing_res.scalar_one_or_none()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        product_res = await self.db.execute(select(PremiumProduct).where(PremiumProduct.key == product_key))
        product = product_res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        now = datetime.now(timezone.utc)
        
        # 2. Apply Effect based on Product Type
        # Logic derived from product key patterns
        
        if "SHOWCASE" in product_key:
            listing.is_showcase = True
            # Extend if already active, else start from now
            current_expiry = listing.showcase_expires_at
            if current_expiry and current_expiry > now:
                new_expiry = current_expiry + timedelta(days=product.duration_days)
            else:
                new_expiry = now + timedelta(days=product.duration_days)
            listing.showcase_expires_at = new_expiry
            
        elif "BOOST" in product_key:
            listing.boosted_at = now
            # Boost doesn't have duration, it's one-off.
            
        elif "URGENT" in product_key:
            listing.is_urgent = True
            current_expiry = listing.urgent_expires_at
            if current_expiry and current_expiry > now:
                new_expiry = current_expiry + timedelta(days=product.duration_days)
            else:
                new_expiry = now + timedelta(days=product.duration_days)
            listing.urgent_expires_at = new_expiry
            
        elif "BOLD" in product_key:
            listing.is_bold_title = True
            # Bold might be permanent or duration based. P17 Matrix said "Listing Duration".
            # So no specific expiry needed, or matches listing expiry.
            
        # 3. Create History Record
        # Calculate end_at for history
        if product.duration_days > 0:
            history_end = now + timedelta(days=product.duration_days)
        else:
            history_end = now # Instant
            
        promotion = ListingPromotion(
            listing_id=listing_id,
            product_id=product.id,
            start_at=now,
            end_at=history_end,
            is_active=True,
            created_by_admin_id=uuid.UUID(admin_id) if admin_id else None
        )
        self.db.add(promotion)
        
        # 4. Invalidate Cache
        from app.core.redis_cache import cache_service
        # Clear search cache because sorting/filtering might change (Showcase/Boost)
        # Ideally we only clear relevant keys, but pattern clearing is safer for MVP
        await cache_service.clear_by_pattern("search:v2:*")
        
        await self.db.commit()
        
        return {"status": "applied", "product": product.key, "listing_id": listing_id}

    async def record_redemption(self, coupon_id: str, user_id: str, order_id: str, amount_discounted: float):
        """
        Finalize redemption. Idempotent via unique constraint.
        """
        # Check uniqueness handled by DB constraint
        import uuid
        
        # Lock Coupon to increment usage
        result = await self.db.execute(select(Coupon).where(Coupon.id == uuid.UUID(coupon_id)).with_for_update())
        coupon = result.scalar_one()
        
        # P14 Abuse Simulation Fix: Double Check Limits inside Transaction Lock
        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
             logger.warning(f"⛔ Redemption Rejected (Limit Reached Race Condition): {coupon.code}")
             # In Stripe logic, payment is done. We can't rollback payment here easily.
             # We should throw error to trigger "failed webhook" -> manual review or auto-refund logic.
             raise HTTPException(status_code=409, detail="Coupon limit reached during finalization")

        redemption = CouponRedemption(
            coupon_id=coupon.id,
            user_id=uuid.UUID(user_id),
            order_id=uuid.UUID(order_id),
            discount_amount=amount_discounted,
            redeemed_at=datetime.now(timezone.utc)
        )
        self.db.add(redemption)
        
        # Increment usage
        coupon.usage_count += 1
        
        await self.db.commit()
        logger.info(f"✅ Coupon {coupon.code} redeemed by {user_id}")

        """
        P17: Applies a premium product to a listing.
        Handles logic for Showcase, Urgent, Bold, and Boost.
        """
        from app.models.moderation import Listing
        from app.models.premium import PremiumProduct, ListingPromotion
        
        # 1. Fetch Listing & Product
        listing_res = await self.db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
        listing = listing_res.scalar_one_or_none()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        product_res = await self.db.execute(select(PremiumProduct).where(PremiumProduct.key == product_key))
        product = product_res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        now = datetime.now(timezone.utc)
        
        # 2. Apply Effect based on Product Type
        # Logic derived from product key patterns
        
        if "SHOWCASE" in product_key:
            listing.is_showcase = True
            # Extend if already active, else start from now
            current_expiry = listing.showcase_expires_at
            if current_expiry and current_expiry > now:
                new_expiry = current_expiry + timedelta(days=product.duration_days)
            else:
                new_expiry = now + timedelta(days=product.duration_days)
            listing.showcase_expires_at = new_expiry
            
        elif "BOOST" in product_key:
            listing.boosted_at = now
            # Boost doesn't have duration, it's one-off.
            
        elif "URGENT" in product_key:
            listing.is_urgent = True
            current_expiry = listing.urgent_expires_at
            if current_expiry and current_expiry > now:
                new_expiry = current_expiry + timedelta(days=product.duration_days)
            else:
                new_expiry = now + timedelta(days=product.duration_days)
            listing.urgent_expires_at = new_expiry
            
        elif "BOLD" in product_key:
            listing.is_bold_title = True
            # Bold might be permanent or duration based. P17 Matrix said "Listing Duration".
            # So no specific expiry needed, or matches listing expiry.
            
        # 3. Create History Record
        # Calculate end_at for history
        if product.duration_days > 0:
            history_end = now + timedelta(days=product.duration_days)
        else:
            history_end = now # Instant
            
        promotion = ListingPromotion(
            listing_id=listing_id,
            product_id=product.id,
            start_at=now,
            end_at=history_end,
            is_active=True,
            created_by_admin_id=uuid.UUID(admin_id) if admin_id else None
        )
        self.db.add(promotion)
        
        # 4. Invalidate Cache
        from app.core.redis_cache import cache_service
        # Clear search cache because sorting/filtering might change (Showcase/Boost)
        # Ideally we only clear relevant keys, but pattern clearing is safer for MVP
        await cache_service.clear_by_pattern("search:v2:*")
        
        await self.db.commit()
        
        return {"status": "applied", "product": product.key, "listing_id": listing_id}
