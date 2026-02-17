from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from app.dependencies import get_db, check_permissions
from app.models.dealer import Dealer
from app.models.user import User
from app.models.commercial import DealerSubscription, DealerPackage

router = APIRouter()

class DealerRevenueStats(BaseModel):
    total_dealers: int
    active_paid_dealers: int
    mrr_estimated: float
    avg_listings_per_dealer: float
    churn_rate_30d: float # Mocked for now

@router.get("/dealer-revenue", response_model=DealerRevenueStats)
async def get_dealer_revenue_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance"]))
):
    # 1. Total Dealers
    total_dealers = (await db.execute(select(func.count(Dealer.id)))).scalar() or 0
    
    # 2. Active Paid Dealers (Mock logic: Dealers with 'active' status and listing_limit > 10)
    # In real world: Join with DealerSubscription
    active_paid = (await db.execute(select(func.count(Dealer.id)).where(
        Dealer.status == 'active',
        Dealer.listing_limit > 10 # Assuming >10 implies paid plan
    ))).scalar() or 0
    
    # 3. MRR Calculation
    # Fetch all active subscriptions
    subs = (await db.execute(select(DealerSubscription).where(DealerSubscription.status == 'active'))).scalars().all()
    mrr = 0.0
    for sub in subs:
        # Fetch package price
        pkg = await db.get(DealerPackage, sub.package_id)
        if pkg:
            mrr += float(pkg.price_net)
            
    # 4. Usage Stats
    avg_listings = 0
    if total_dealers > 0:
        total_listings = (await db.execute(select(func.sum(Dealer.active_listing_count)))).scalar() or 0
        avg_listings = total_listings / total_dealers

    return DealerRevenueStats(
        total_dealers=total_dealers,
        active_paid_dealers=active_paid,
        mrr_estimated=mrr,
        avg_listings_per_dealer=avg_listings,
        churn_rate_30d=2.5 # Mock benchmark
    )
