from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel

from app.dependencies import get_db
from app.models.dealer import Dealer
from app.models.moderation import Listing
from app.models.user import User
from app.routers.public.search_routes import SearchResult

router = APIRouter()

class DealerProfileResponse(BaseModel):
    id: str
    company_name: str
    slug: str
    logo_url: Optional[str]
    description: Optional[str]
    location: dict
    contact: dict
    badges: List[str]
    stats: dict
    listings: List[SearchResult]

@router.get("/{slug}", response_model=DealerProfileResponse)
async def get_dealer_profile(
    slug: str,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Dealer
    query = select(Dealer).where(Dealer.slug == slug, Dealer.status == 'active')
    dealer = (await db.execute(query)).scalar_one_or_none()
    
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
        
    # 2. Fetch User (Owner) for verification status (optional merge)
    user = await db.get(User, dealer.user_id)
    
    # 3. Fetch Listings
    l_query = select(Listing).where(
        Listing.dealer_id == dealer.id,
        Listing.status == 'active'
    ).order_by(desc(Listing.created_at)).offset((page-1)*limit).limit(limit)
    
    l_result = await db.execute(l_query)
    listings = l_result.scalars().all()
    
    # Map Listings to SearchResult
    listing_dtos = []
    for l in listings:
        specs = {}
        if l.attributes:
            if "m2_gross" in l.attributes: specs["m2"] = l.attributes["m2_gross"]
            if "room_count" in l.attributes: specs["rooms"] = l.attributes["room_count"]
            
        badges = []
        if l.is_premium: badges.append("premium")
        
        listing_dtos.append(SearchResult(
            id=str(l.id),
            title=l.title,
            price=float(l.price) if l.price else 0,
            currency=l.currency,
            location={"city": l.city, "country": l.country},
            specs=specs,
            image_url=l.images[0] if l.images else None,
            published_at=l.created_at.isoformat() if l.created_at else "",
            badges=badges
        ))

    # 4. Construct Response
    return DealerProfileResponse(
        id=str(dealer.id),
        company_name=dealer.company_name,
        slug=dealer.slug,
        logo_url=dealer.logo_url,
        description=getattr(dealer, 'description', None), # Assuming description added or handled in previous migrations
        location={
            # "address": dealer.address, # Need to check if address column exists in Dealer model G1
            "country": dealer.country
        },
        contact={
            "website": getattr(dealer, 'website', None),
            # "phone": dealer.phone # Check model
        },
        badges=["verified"] if dealer.verified_at else [],
        stats={
            "total_listings": dealer.active_listing_count or 0
        },
        listings=listing_dtos
    )
