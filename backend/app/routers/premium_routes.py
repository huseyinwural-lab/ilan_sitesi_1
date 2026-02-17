
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.premium import PremiumProduct
from app.models.moderation import Listing
from app.services.quota_service import QuotaService, QuotaExceededError
from app.services.promotion_service import PromotionService
from pydantic import BaseModel
from typing import Optional
import uuid
import stripe
import os
import logging

router = APIRouter(prefix="/v1/premium", tags=["premium"])
logger = logging.getLogger(__name__)

# Config
stripe.api_key = os.environ.get("STRIPE_API_KEY")
DOMAIN = os.environ.get("FRONTEND_URL", "http://localhost:3000")

class PromoteRequest(BaseModel):
    listing_id: str
    product_key: str

@router.get("/products")
async def get_premium_products(
    country: str = "TR", 
    db: AsyncSession = Depends(get_db)
):
    stmt = select(PremiumProduct).where(PremiumProduct.country == country.upper(), PremiumProduct.is_active == True).order_by(PremiumProduct.sort_order)
    res = await db.execute(stmt)
    products = res.scalars().all()
    
    return [{
        "key": p.key,
        "name": p.name,
        "description": p.description,
        "price": float(p.price_net),
        "currency": p.currency,
        "duration_days": p.duration_days
    } for p in products]

@router.post("/promote")
async def promote_listing(
    data: PromoteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Apply premium product to listing.
    Tries to use Quota first. If not available, returns Checkout URL.
    """
    # 1. Fetch Product & Listing
    prod_stmt = select(PremiumProduct).where(PremiumProduct.key == data.product_key)
    prod = (await db.execute(prod_stmt)).scalar_one_or_none()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
        
    list_stmt = select(Listing).where(Listing.id == uuid.UUID(data.listing_id))
    listing = (await db.execute(list_stmt)).scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    if listing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    promo_service = PromotionService(db)
    quota_service = QuotaService(db)
    
    # 2. Try Quota (Only for Showcase currently supported in QuotaService)
    # P17 Dealer Matrix: "Showcase Hakkı".
    # We map product_key to resource name.
    # Logic: If product is SHOWCASE_*, we check "showcase_active".
    # Boost/Urgent quotas not yet implemented in QuotaService (P17 scope limitation).
    # We can assume only Showcase consumes quota for now.
    
    quota_consumed = False
    
    if "SHOWCASE" in data.product_key:
        try:
            # Check if user has quota
            # Consume 1 unit.
            # Note: QuotaService checks "Active" count.
            # Applying a showcase INCREASES active count.
            # So calling consume_quota does exactly that.
            
            # Transactional Check & Consume
            async with db.begin_nested():
                await quota_service.consume_quota(str(current_user.id), "showcase_active", 1)
                quota_consumed = True
                
                # Apply immediately
                await promo_service.apply_promotion(data.listing_id, data.product_key)
                
            return {"status": "applied", "method": "quota"}
            
        except QuotaExceededError:
            # Quota full, fall through to Payment
            pass
        except Exception as e:
            logger.error(f"Quota error: {e}")
            pass

    # 3. Payment Flow (Stripe Checkout)
    # If not consumed via quota, we charge.
    
    # Get Customer
    from app.models.billing import BillingCustomer
    cus_stmt = select(BillingCustomer).where(BillingCustomer.user_id == current_user.id)
    billing_cus = (await db.execute(cus_stmt)).scalar_one_or_none()
    
    customer_id = None
    if billing_cus:
        customer_id = billing_cus.stripe_customer_id
    else:
        # Create Customer on fly? Or require billing setup?
        # For better UX, create on fly or let Checkout create it (if email provided).
        # We prefer attaching to our user.
        try:
            stripe_cus = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            new_cus = BillingCustomer(user_id=current_user.id, stripe_customer_id=stripe_cus.id)
            db.add(new_cus)
            await db.commit()
            customer_id = stripe_cus.id
        except Exception as e:
            logger.error(f"Stripe Customer Error: {e}")
            raise HTTPException(status_code=502, detail="Payment Provider Error")

    # Create Session
    try:
        # Product Name localization
        prod_name = prod.name.get("tr", prod.key) # Fallback
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": prod.currency.lower(),
                    "product_data": {
                        "name": prod_name,
                        "description": prod.description.get("tr", "") if prod.description else None
                    },
                    "unit_amount": int(prod.price_net * 100), # Cents
                },
                "quantity": 1,
            }],
            mode="payment", # One-time payment
            success_url=f"{DOMAIN}/dashboard/listings?promote=success",
            cancel_url=f"{DOMAIN}/dashboard/listings?promote=cancel",
            client_reference_id=str(current_user.id),
            metadata={
                "type": "premium_purchase",
                "listing_id": data.listing_id,
                "product_key": data.product_key
            }
        )
        
        return {"status": "payment_required", "checkout_url": session.url}
        
    except Exception as e:
        logger.error(f"Stripe Checkout Error: {e}")
        raise HTTPException(status_code=502, detail=f"Payment Error: {str(e)}")
