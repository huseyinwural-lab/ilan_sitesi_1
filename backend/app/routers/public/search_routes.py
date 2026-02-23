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
    
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    use_listings_search = _use_listings_search(request)
    ListingModel = ListingSearch if use_listings_search else Listing
    price_col = ListingSearch.price_amount if use_listings_search else Listing.price
    price_type_col = ListingSearch.price_type if use_listings_search else Listing.price_type
    country_col = ListingSearch.country_code if use_listings_search else Listing.country
    module_col = ListingSearch.module if use_listings_search else Listing.module
    city_col = ListingSearch.city if use_listings_search else Listing.city
    created_col = ListingSearch.published_at if use_listings_search else Listing.created_at
    premium_col = ListingSearch.is_premium if use_listings_search else Listing.is_premium

    query = select(ListingModel).where(
        ListingModelisting.status == 'active',
        country_col == country.upper(),
        module_col == 'real_estate' # or 'residential', need to align with Category seed
    )

    # Filters
    if city:
        query = query.where(city_colisting.ilike(f"%{city}%"))
    if price_min:
        query = query.where(price_col >= price_min)
    if price_max:
        query = query.where(price_col <= price_max)
    if price_min or price_max:
        query = query.where(or_(price_type_col == "FIXED", price_type_colisting.is_(None)))

    # Sorting
    if sort == "price_asc":
        query = query.order_by(price_colisting.asc())
    elif sort == "price_desc":
        query = query.order_by(price_colisting.desc())
    else: # newest
        query = query.order_by(desc(premium_col), desc(created_col))

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    listings = result.scalars().all()
    
    # Map Response
    data = []
    for listing in listings:
        # Extract m2 and rooms from attributes if available
        specs = {}
        attributes = listing.attributes or {}
        if "m2_gross" in attributes:
            specs["m2"] = attributes["m2_gross"]
        if "room_count" in attributes:
            specs["rooms"] = attributes["room_count"]

        badges = []
        if listing.is_premium:
            badges.append("premium")
        if use_listings_search:
            if (listing.seller_type or "") == "commercial":
                badges.append("commercial")
        else:
            if listing.user_type_snapshot == "commercial":
                badges.append("commercial")

        price_value = listing.price_amount if use_listings_search else listing.price
        currency_value = listing.currency or "EUR"
        price_type_value = listing.price_type or "FIXED"
        location_country = listing.country_code if use_listings_search else listing.country
        published_at = listing.published_at if use_listings_search else listing.created_at

        data.append(SearchResult(
            id=str(listing.listing_id if use_listings_search else listing.id),
            title=listing.title,
            price=float(price_value) if price_value is not None else None,
            price_type=price_type_value,
            price_amount=float(price_value) if price_value is not None else None,
            hourly_rate=float(listing.hourly_rate) if listing.hourly_rate is not None else None,
            currency=currency_value,
            location={"city": listing.city, "country": location_country},
            specs=specs,
            image_url=listing.images[0] if listing.images else None,
            published_at=published_at.isoformat() if published_at else "",
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
