
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.affiliate import Affiliate, AffiliateClick
from app.models.ledger import RewardLedger
from app.models.referral import ConversionEvent
import uuid

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate-dashboard"])

@router.get("/dashboard")
async def get_affiliate_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Affiliate performance stats.
    """
    if not current_user.is_affiliate:
        return {"status": "not_affiliate"}
        
    stmt = select(Affiliate).where(Affiliate.user_id == current_user.id)
    affiliate = (await db.execute(stmt)).scalar_one()
    
    # 1. Clicks
    click_stmt = select(func.count(AffiliateClick.id)).where(AffiliateClick.affiliate_id == affiliate.id)
    clicks = (await db.execute(click_stmt)).scalar() or 0
    
    # 2. Conversions (Referred Users)
    conv_stmt = select(func.count(User.id)).where(User.referred_by_affiliate_id == affiliate.id)
    conversions = (await db.execute(conv_stmt)).scalar() or 0
    
    # 3. Earnings (Ledger)
    # Filter by user_id = affiliate.user_id AND reason startswith 'affiliate_commission'
    earn_stmt = select(func.sum(RewardLedger.amount)).where(
        and_(
            RewardLedger.user_id == affiliate.user_id,
            RewardLedger.type == 'CREDIT',
            RewardLedger.reason.like('affiliate_commission%')
        )
    )
    earnings = (await db.execute(earn_stmt)).scalar() or 0
    
    # 4. Pending vs Paid?
    # In P18 we credit immediately to Stripe Balance (Negative Balance).
    # So "Earnings" are basically "credited".
    # Withdrawal is handled by P16 logic (Net Balance).
    
    return {
        "slug": affiliate.custom_slug,
        "clicks": clicks,
        "conversions": conversions,
        "total_earnings": float(earnings),
        "commission_rate": float(affiliate.commission_rate),
        "link": f"/ref/{affiliate.custom_slug}"
    }
