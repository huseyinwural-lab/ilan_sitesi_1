
import os
import stripe
import logging
from fastapi import APIRouter, Header, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.dependencies import get_db
from app.models.billing import StripeEvent, StripeSubscription, BillingCustomer
from app.models.monetization import UserSubscription, SubscriptionPlan
from datetime import datetime, timezone

router = APIRouter(prefix="/v1/billing", tags=["billing"])
logger = logging.getLogger(__name__)

STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_mock")

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Idempotency Check
    stmt = select(StripeEvent).where(StripeEvent.id == event.id)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        return {"status": "idempotent"}

    # Process Event
    try:
        if event.type == 'checkout.session.completed':
            await handle_checkout_completed(event.data.object, db)
        elif event.type == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event.data.object, db)
        elif event.type == 'customer.subscription.deleted':
            await handle_subscription_deleted(event.data.object, db)
            
        # Log Event
        db.add(StripeEvent(id=event.id, type=event.type, status="processed"))
        await db.commit()
        
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        # Log failure but return 200 to Stripe to avoid retries if it's a logic bug? 
        # Ideally 500 triggers retry. Let's return 500 for retryable errors.
        await db.rollback()
        raise HTTPException(status_code=500, detail="Processing error")

    return {"status": "success"}

# --- Handlers ---

async def handle_checkout_completed(session, db):
    # Activate Subscription
    user_id = session.get("client_reference_id")
    sub_id = session.get("subscription")
    plan_code = session.get("metadata", {}).get("plan_code")
    
    if not user_id or not sub_id or not plan_code:
        logger.error("Missing metadata in checkout session")
        return

    # Create/Update StripeSubscription
    # Fetch Plan ID
    plan_res = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code))
    plan = plan_res.scalar_one_or_none()
    
    if not plan:
        logger.error(f"Plan {plan_code} not found")
        return

    # Update UserSubscription (Domain)
    # Deactivate old ones? Or logic handles 'active' status priority
    
    new_sub = UserSubscription(
        user_id=uuid.UUID(user_id),
        plan_id=plan.id,
        status="active",
        start_at=datetime.now(timezone.utc),
        # Real logic should fetch subscription details for end_at
        end_at=datetime.fromtimestamp(session.get("expires_at", 0) or 0, tz=timezone.utc), 
        auto_renew=True
    )
    db.add(new_sub)
    
    # Also store Stripe mapping
    stripe_sub = StripeSubscription(
        id=sub_id,
        user_id=uuid.UUID(user_id),
        plan_code=plan_code,
        status="active",
        current_period_end=datetime.now(timezone.utc) # Placeholder, ideally fetch sub
    )
    db.add(stripe_sub)

async def handle_payment_succeeded(invoice, db):
    sub_id = invoice.get("subscription")
    if not sub_id: return
    
    # Update End Date
    end_date = datetime.fromtimestamp(invoice["lines"]["data"][0]["period"]["end"], tz=timezone.utc)
    
    # Update StripeSub
    s_stmt = select(StripeSubscription).where(StripeSubscription.id == sub_id)
    res = await db.execute(s_stmt)
    stripe_sub = res.scalar_one_or_none()
    
    if stripe_sub:
        stripe_sub.current_period_end = end_date
        stripe_sub.status = "active"
        
        # Update UserSubscription
        # Link via user_id + plan?
        u_stmt = select(UserSubscription).where(UserSubscription.user_id == stripe_sub.user_id, UserSubscription.status == 'active')
        u_res = await db.execute(u_stmt)
        user_sub = u_res.scalar_one_or_none()
        if user_sub:
            user_sub.end_at = end_date

async def handle_subscription_deleted(sub, db):
    sub_id = sub["id"]
    # Mark expired
    # ... implementation logic
    pass
