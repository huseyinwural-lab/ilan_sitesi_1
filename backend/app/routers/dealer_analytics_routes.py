from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta, timezone
from typing import List
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user, check_permissions
from app.models.user import User
from app.models.dealer import Dealer
from app.models.moderation import Listing
from app.models.analytics import ListingView, UserInteraction

router = APIRouter()

class DealerAnalyticsSummary(BaseModel):
    total_listings: int
    active_listings: int
    total_views: int
    total_contacts: int
    avg_cost_per_lead: float
    spend_last_30d: float

@router.get("/overview", response_model=DealerAnalyticsSummary)
async def get_dealer_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["dealer_admin"]))
):
    # 1. Get Dealer Profile
    dealer = (await db.execute(select(Dealer).where(Dealer.user_id == current_user.id))).scalar_one_or_none()
    # Or link via DealerUser table if multiple users per dealer
    # For MVP, assuming direct link or we fetch via helper
    if not dealer:
        # Try to find via DealerUser
        from app.models.dealer import DealerUser
        du = (await db.execute(select(DealerUser).where(DealerUser.user_id == current_user.id))).scalar_one_or_none()
        if du:
            dealer = (await db.execute(select(Dealer).where(Dealer.id == du.dealer_id))).scalar_one_or_none()
            
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer profile not found")

    # 2. Listings Stats
    listings_query = select(Listing).where(Listing.dealer_id == dealer.id)
    listings = (await db.execute(listings_query)).scalars().all()
    listing_ids = [l.id for l in listings]
    
    if not listing_ids:
        return DealerAnalyticsSummary(
            total_listings=0, active_listings=0, total_views=0, total_contacts=0, avg_cost_per_lead=0.0, spend_last_30d=0.0
        )

    # 3. Aggregates (Last 30 Days)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Views (Using ListingView or Listing.view_count)
    # Using real-time Aggregation from UserInteraction for precision
    views = (await db.execute(select(func.count(UserInteraction.id)).where(
        UserInteraction.listing_id.in_(listing_ids),
        UserInteraction.event_type == 'listing_viewed',
        UserInteraction.created_at >= cutoff
    ))).scalar() or 0
    
    contacts = (await db.execute(select(func.count(UserInteraction.id)).where(
        UserInteraction.listing_id.in_(listing_ids),
        UserInteraction.event_type == 'listing_contact_clicked',
        UserInteraction.created_at >= cutoff
    ))).scalar() or 0
    
    # Mock Spend Calculation (In real app, query Invoice items)
    spend = 150.00 # Placeholder
    
    cpl = spend / contacts if contacts > 0 else 0.0
    
    return DealerAnalyticsSummary(
        total_listings=len(listings),
        active_listings=sum(1 for l in listings if l.status == 'active'),
        total_views=views,
        total_contacts=contacts,
        avg_cost_per_lead=cpl,
        spend_last_30d=spend
    )
