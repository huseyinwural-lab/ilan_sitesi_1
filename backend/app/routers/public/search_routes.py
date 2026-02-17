from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, or_, func
from typing import Optional, List
from app.dependencies import get_db
from app.models.moderation import Listing
from pydantic import BaseModel

router = APIRouter()

class SearchResult(BaseModel):
    id: str
    title: str
    price: Optional[float]
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
            price=float(l.price) if l.price else 0,
            currency=l.currency,
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
