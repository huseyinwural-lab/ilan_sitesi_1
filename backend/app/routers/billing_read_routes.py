
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.monetization import UserSubscription, SubscriptionPlan, QuotaUsage
from app.services.quota_service import QuotaService

router = APIRouter(prefix="/v1/billing", tags=["billing"])
logger = logging.getLogger(__name__)

@router.get("/subscription")
async def get_subscription_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current subscription status and usage for UI.
    """
    qs = QuotaService(db)
    
    # 1. Get Limits
    limits = await qs.get_limits(str(current_user.id))
    
    # 2. Get Usage
    usage_listing = await qs.get_usage(str(current_user.id), "listing_active")
    
    # 3. Get Plan Details
    sub = await qs._get_active_subscription(str(current_user.id))
    
    if sub:
        plan_res = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
        plan = plan_res.scalar_one()
        
        return {
            "status": sub.status,
            "code": plan.code,
            "plan": {
                "name": plan.name,
                "price": float(plan.price),
                "currency": plan.currency
            },
            "limits": limits,
            "usage": {
                "listing_active": usage_listing
            },
            "current_period_end": sub.end_at.isoformat() if sub.end_at else None
        }
    else:
        # Free Plan
        return {
            "status": "free",
            "code": "FREE",
            "plan": {
                "name": {"en": "Free Plan", "tr": "Ücretsiz Paket"},
                "price": 0,
                "currency": "TRY"
            },
            "limits": limits,
            "usage": {
                "listing_active": usage_listing
            },
            "current_period_end": None
        }
