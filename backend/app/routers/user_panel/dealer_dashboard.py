from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user, check_permissions
from app.models.user import User
from app.models.dealer import Dealer
from app.models.moderation import Listing
from app.models.analytics import UserInteraction

router = APIRouter()

class DealerDashboardStats(BaseModel):
    active_listings: int
    listing_limit: int
    showcase_remaining: int
    total_views_30d: int
    total_leads_30d: int
    plan_name: str

class DealerLead(BaseModel):
    id: str
    type: str # message, phone_reveal
    listing_title: str
    listing_id: str
    user_name: Optional[str]
    created_at: str

@router.get("/dashboard", response_model=DealerDashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Get Dealer
    dealer = (await db.execute(select(Dealer).where(Dealer.user_id == current_user.id))).scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=403, detail="Not a dealer account")

    # 2. Inventory Stats
    active_count = (await db.execute(select(func.count(Listing.id)).where(
        Listing.dealer_id == dealer.id, 
        Listing.status == 'active'
    ))).scalar()
    
    # 3. Analytics (30d)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Get Listing IDs
    listings_res = await db.execute(select(Listing.id).where(Listing.dealer_id == dealer.id))
    listing_ids = listings_res.scalars().all()
    
    views = 0
    leads = 0
    
    if listing_ids:
        # Views
        views = (await db.execute(select(func.count(UserInteraction.id)).where(
            UserInteraction.listing_id.in_(listing_ids),
            UserInteraction.event_type == 'listing_viewed',
            UserInteraction.created_at >= cutoff
        ))).scalar()
        
        # Leads (Message + Phone)
        leads = (await db.execute(select(func.count(UserInteraction.id)).where(
            UserInteraction.listing_id.in_(listing_ids),
            UserInteraction.event_type.in_(['listing_contact_clicked', 'message_sent']), # Assuming 'message_sent' maps to interaction
            UserInteraction.created_at >= cutoff
        ))).scalar()

    return DealerDashboardStats(
        active_listings=active_count,
        listing_limit=dealer.listing_limit,
        showcase_remaining=dealer.premium_limit, # Simplified
        total_views_30d=views,
        total_leads_30d=leads,
        plan_name="Standard" # Placeholder
    )

@router.get("/leads", response_model=List[DealerLead])
async def get_dealer_leads(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dealer = (await db.execute(select(Dealer).where(Dealer.user_id == current_user.id))).scalar_one_or_none()
    if not dealer:
        raise HTTPException(status_code=403, detail="Not a dealer")
        
    # Get Listing IDs
    listings_res = await db.execute(select(Listing.id).where(Listing.dealer_id == dealer.id))
    listing_ids = listings_res.scalars().all()
    
    if not listing_ids:
        return []
        
    # Fetch Interactions
    query = select(UserInteraction, Listing.title).join(Listing, UserInteraction.listing_id == Listing.id).where(
        UserInteraction.listing_id.in_(listing_ids),
        UserInteraction.event_type.in_(['listing_contact_clicked', 'message_sent'])
    ).order_by(desc(UserInteraction.created_at)).offset((page-1)*limit).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    leads = []
    for interaction, title in rows:
        leads.append(DealerLead(
            id=str(interaction.id),
            type="phone_reveal" if interaction.event_type == 'listing_contact_clicked' else "message",
            listing_title=title,
            listing_id=str(interaction.listing_id),
            user_name="Guest User", # Needs User join if logged in
            created_at=interaction.created_at.isoformat()
        ))
        
    return leads
