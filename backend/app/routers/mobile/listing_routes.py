from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.category import Category

from app.middleware.mobile_rate_limit import mobile_rate_limiter
router = APIRouter()

# --- DTOs ---
class MobileListingCard(BaseModel):
    id: str
    title: str
    price: float
    currency: str
    image_url: Optional[str]
    location: str
    date: str
    is_premium: bool

class MobileFeedResponse(BaseModel):
    data: List[MobileListingCard]
    meta: dict

# --- Endpoints ---
@router.get("/feed", response_model=MobileFeedResponse, dependencies=[Depends(mobile_rate_limiter)])
async def get_mobile_feed(
    response: Response,
    page: int = 1,
    limit: int = 20,
    country: str = "TR",
    category_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Set Cache-Control header
    response.headers["Cache-Control"] = "public, max-age=60"

    skip = (page - 1) * limit
    
    query = select(Listing).where(Listing.status == 'active')
    
    # Country Filter
    query = query.where(Listing.country == country.upper())
    
    # Category Filter
    if category_id:
        query = query.where(Listing.category_id == uuid.UUID(category_id))
        
    # Sort
    query = query.order_by(desc(Listing.is_premium), desc(Listing.created_at))
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    listings = result.scalars().all()
    
    # Map to DTO
    data = []
    for l in listings:
        data.append(MobileListingCard(
            id=str(l.id),
            title=l.title,
            price=float(l.price),
            currency=l.currency,
            image_url=l.images[0] if l.images else None, # First image as thumb
            location=f"{l.city}, {l.country}",
            date=l.created_at.strftime("%Y-%m-%d") if l.created_at else "",
            is_premium=l.is_premium
        ))
        
    return {
        "data": data,
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(data),
            "has_more": len(data) == limit
        }
    }

class MobileListingDetail(BaseModel):
    id: str
    title: str
    description: str
    price: dict
    images: List[dict]
    attributes: List[dict]
    seller: dict
    is_favorite: bool

@router.get("/{listing_id}", response_model=MobileListingDetail)
async def get_mobile_listing_detail(
    listing_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    # Set Cache-Control header (5 mins)
    response.headers["Cache-Control"] = "public, max-age=300"
    
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    return {
        "id": str(listing.id),
        "title": listing.title,
        "description": listing.description or "",
        "price": {
            "value": float(listing.price),
            "currency": listing.currency,
            "formatted": f"{float(listing.price):,.0f} {listing.currency}"
        },
        "images": [{"url": img, "type": "original"} for img in (listing.images or [])],
        "attributes": [{"label": k, "value": str(v)} for k, v in (listing.attributes or {}).items()],
        "seller": {
            "id": str(listing.user_id),
            "type": "individual", # Simplified for MVP
            "name": "Seller" # Ideally fetch User name
        },
        "is_favorite": False # Placeholder
    }
