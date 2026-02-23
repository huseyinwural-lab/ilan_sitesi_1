from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_, func
from typing import Optional, List
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.listing_search import ListingSearch
from pydantic import BaseModel
import os
import hashlib

router = APIRouter()


def _get_search_sql_rollout() -> float:
    try:
        rollout = float(os.environ.get("SEARCH_SQL_ROLLOUT", "0"))
    except ValueError:
        rollout = 0.0
    return max(0.0, min(1.0, rollout))


def _stable_bucket_for_request(request) -> float:
    key = None
    if request:
        key = request.headers.get("X-Request-ID")
        if not key and request.client:
            key = request.client.host
    if not key:
        key = "anonymous"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    bucket_int = int(digest[:8], 16)
    return bucket_int / 0xFFFFFFFF


def _use_listings_search(request) -> bool:
    rollout = _get_search_sql_rollout()
    if rollout >= 1:
        return True
    if rollout <= 0:
        return False
    return _stable_bucket_for_request(request) < rollout

class SearchResult(BaseModel):
    id: str
    title: str
    price: Optional[float]
    price_type: Optional[str]
    price_amount: Optional[float]
    hourly_rate: Optional[float]
    currency: str
    location: dict
    specs: dict
    image_url: Optional[str]
    published_at: str
    badges: List[str]

class SearchResponse(BaseModel):
    data: List[SearchResult]
    meta: dict

from app.utils.cache import cache_search

@router.get("/real-estate", response_model=SearchResponse)
@cache_search(ttl_seconds=60) # 1 min cache for search
async def search_real_estate(
    country: str = Query(..., min_length=2, max_length=2),
    # Taxonomy
    # segment: Optional[str] = None, # Not in Listing model yet as direct column, implied by Category?
    # For MVP, we filter by Module = 'real_estate'
    
    # Filters
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    city: Optional[str] = None,
    
    # Sort
    sort: str = "newest",
    limit: int = 20,
    page: int = 1,
    
    db: AsyncSession = Depends(get_db)
):
    query = select(Listing).where(
        Listing.status == 'active',
        Listing.country == country.upper(),
        Listing.module == 'real_estate' # or 'residential', need to align with Category seed
    )
    
    # Filters
    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    if price_min:
        query = query.where(Listing.price >= price_min)
    if price_max:
        query = query.where(Listing.price <= price_max)
    if price_min or price_max:
        query = query.where(or_(Listing.price_type == "FIXED", Listing.price_type.is_(None)))
        
    # Sorting
    if sort == "price_asc":
        query = query.order_by(Listing.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Listing.price.desc())
    else: # newest
        query = query.order_by(desc(Listing.is_premium), desc(Listing.created_at))
        
    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    listings = result.scalars().all()
    
    # Map Response
    data = []
    for l in listings:
        # Extract m2 and rooms from attributes if available
        specs = {}
        if l.attributes:
            if "m2_gross" in l.attributes: specs["m2"] = l.attributes["m2_gross"]
            if "room_count" in l.attributes: specs["rooms"] = l.attributes["room_count"]
            
        badges = []
        if l.is_premium: badges.append("premium")
        if l.user_type_snapshot == "commercial": badges.append("commercial")
        
        data.append(SearchResult(
            id=str(l.id),
            title=l.title,
            price=float(l.price) if l.price is not None else None,
            price_type=l.price_type or "FIXED",
            price_amount=float(l.price) if l.price is not None else None,
            hourly_rate=float(l.hourly_rate) if l.hourly_rate is not None else None,
            currency=l.currency or "EUR",
            location={"city": l.city, "country": l.country},
            specs=specs,
            image_url=l.images[0] if l.images else None,
            published_at=l.created_at.isoformat() if l.created_at else "",
            badges=badges
        ))
        
    return {
        "data": data,
        "meta": {
            "page": page,
            "limit": limit,
            "count": len(data) # Total count query skipped for MVP speed
        }
    }
