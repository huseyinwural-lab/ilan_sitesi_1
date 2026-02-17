
import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.billing import BillingCustomer
from pydantic import BaseModel
import logging

router = APIRouter(prefix="/v1/billing", tags=["billing"])
logger = logging.getLogger(__name__)

# Config
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_mock")
DOMAIN = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# Product Mapping (Simple Dict for MVP)
PLAN_MAP = {
    "TR_DEALER_BASIC": "price_basic_tr_mo",
    "TR_DEALER_PRO": "price_pro_tr_mo",
    "TR_DEALER_ENTERPRISE": "price_ent_tr_mo"
}

class CheckoutRequest(BaseModel):
    plan_code: str
    coupon_code: str | None = None

@router.post("/checkout")
async def create_checkout_session(
    data: CheckoutRequest, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create Stripe Checkout Session for Subscription.
    """
    # ... (existing imports)
    from app.services.stripe_service import StripeService
    # ...
    
    price_id = PLAN_MAP.get(data.plan_code)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid Plan Code")

    # 1. Get/Create Customer (Existing logic)
    stmt = select(BillingCustomer).where(BillingCustomer.user_id == current_user.id)
    res = await db.execute(stmt)
    billing_cus = res.scalar_one_or_none()
    
    if not billing_cus:
        # Create in Stripe (Existing logic)
        try:
            stripe_cus = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            billing_cus = BillingCustomer(
                user_id=current_user.id,
                stripe_customer_id=stripe_cus.id
            )
            db.add(billing_cus)
            await db.commit()
        except Exception as e:
            logger.error(f"Stripe Customer Create Error: {e}")
            raise HTTPException(status_code=502, detail="Payment Provider Error")

    # 2. Create Session via Service (Updated)
    stripe_service = StripeService(db)
    
    # We delegate session creation to service entirely or call logic here?
    # The existing stripe_service.create_checkout_session was for INVOICES (P11).
    # This endpoint is for SUBSCRIPTIONS (P12).
    # I should update THIS endpoint logic to handle coupons, or move subscription checkout to service.
    # Moving to service is cleaner. But let's implement inline here for P14 scope to modify billing_routes.py directly
    # and call promotion_service.
    
    from app.services.promotion_service import PromotionService
    promo_service = PromotionService(db)
    discounts = []
    
    if data.coupon_code:
        # Validate
        coupon, promo = await promo_service.validate_coupon(data.coupon_code, str(current_user.id))
        
        # Get Stripe ID
        stripe_coupon_id = await promo_service.get_or_create_stripe_coupon(promo)
        
        # Prepare param
        discounts.append({"coupon": stripe_coupon_id})

    try:
        session = stripe.checkout.Session.create(
            customer=billing_cus.stripe_customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{DOMAIN}/admin?checkout=success",
            cancel_url=f"{DOMAIN}/admin?checkout=cancel",
            client_reference_id=str(current_user.id),
            metadata={
                "plan_code": data.plan_code,
                "coupon_code": data.coupon_code if data.coupon_code else None
            },
            discounts=discounts
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Stripe Session Error: {e}")
        raise HTTPException(status_code=502, detail=f"Payment Provider Error: {str(e)}")

@router.post("/portal")
async def create_portal_session(
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create Self-Service Portal Session.
    """
    stmt = select(BillingCustomer).where(BillingCustomer.user_id == current_user.id)
    res = await db.execute(stmt)
    billing_cus = res.scalar_one_or_none()
    
    if not billing_cus:
        raise HTTPException(status_code=404, detail="No billing account found")

    try:
        session = stripe.billing_portal.Session.create(
            customer=billing_cus.stripe_customer_id,
            return_url=f"{DOMAIN}/admin"
        )
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Stripe Portal Error: {e}")
        raise HTTPException(status_code=502, detail="Payment Provider Error")
