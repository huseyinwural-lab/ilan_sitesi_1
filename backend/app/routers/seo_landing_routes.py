
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from app.dependencies import get_db
from app.models.category import Category
from app.models.moderation import Listing
from app.core.redis_cache import cache_service
import re

router = APIRouter(tags=["seo-landing"])

# Helper: Slug Normalizer
def normalize_slug(text: str) -> str:
    # Basic ASCII conversion
    replacements = {
        'ş': 's', 'ı': 'i', 'ü': 'u', 'ö': 'o', 'ç': 'c', 'ğ': 'g',
        'Ş': 's', 'İ': 'i', 'Ü': 'u', 'Ö': 'o', 'Ç': 'c', 'Ğ': 'g'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.lower().strip()

# Helper: Price Parser
def parse_price_range(price_slug: str):
    # Pattern: 100k-500k, 1m-plus, under-500k
    min_price = None
    max_price = None
    
    def val(s):
        if not s: return None
        mul = 1
        if s.endswith('k'): mul = 1000; s = s[:-1]
        elif s.endswith('m'): mul = 1000000; s = s[:-1]
        try:
            return int(float(s) * mul)
        except:
            return None

    if "-plus" in price_slug:
        parts = price_slug.split("-plus")
        min_price = val(parts[0])
    elif "under-" in price_slug:
        parts = price_slug.split("under-")
        max_price = val(parts[1])
    elif "-" in price_slug:
        parts = price_slug.split("-")
        if len(parts) == 2:
            min_price = val(parts[0])
            max_price = val(parts[1])
            
    if min_price is None and max_price is None:
        return None # Invalid
        
    return min_price, max_price

@router.get("/landing/{city}/{category}")
@router.get("/landing/{city}/{category}/{price_range}")
async def seo_landing_page(
    city: str,
    category: str,
    price_range: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Programmatic SEO Landing Page.
    Pattern: /{city}/{category}/{price-range?}
    """
    # 1. Normalize Check
    if city != city.lower() or category != category.lower() or (price_range and price_range != price_range.lower()):
        # Canonical Redirect logic would be here (301)
        # For MVP, assume strict contract or 404
        pass

    # 2. Validate City (Whitelist)
    # Simple whitelist for MVP. Ideally DB lookup.
    # We assume 'istanbul', 'ankara' etc. are valid slugs.
    # In production this should check a Cities table.
    # For now, just allow string but we rely on data existence.
    # Wait, we need to map slug to city name in DB (e.g. istanbul -> Istanbul).
    city_map = {"istanbul": "Istanbul", "ankara": "Ankara", "izmir": "Izmir"}
    db_city = city_map.get(city)
    # If not in whitelist, maybe check DB distinctive cities?
    # Let's verify against listings existing cities? Expensive.
    # Rule: If city not known, 404.
    if not db_city:
        # Fallback: Allow any city slug, capitalize for query?
        db_city = city.title() 

    # 3. Validate Category
    # Find category by slug (en or tr)
    # Assuming category structure has 'slug' JSON
    # We need to find category where slug->>'en' == category OR slug->>'tr' == category
    # Simple approach: Fetch all cats cached? Or query.
    # Query:
    # Note: JSONB query depends on dialect.
    # Using python filter for MVP safety if few categories.
    cat_res = await db.execute(select(Category))
    categories = cat_res.scalars().all()
    
    target_cat = None
    for c in categories:
        if c.slug.get('en') == category or c.slug.get('tr') == category:
            target_cat = c
            break
            
    if not target_cat:
        raise HTTPException(status_code=404, detail="Category not found")

    # 4. Parse Price
    p_min, p_max = None, None
    if price_range:
        parsed = parse_price_range(price_range)
        if not parsed:
            raise HTTPException(status_code=404, detail="Invalid price format")
        p_min, p_max = parsed

    # 5. Build Query (The Engine)
    query = select(Listing).where(
        Listing.status == 'active',
        Listing.category_id == target_cat.id,
        func.lower(Listing.city) == city.lower() # Case insensitive match
    )
    
    if p_min: query = query.where(Listing.price >= p_min)
    if p_max: query = query.where(Listing.price <= p_max)
    
    # Sort by Popularity (View Count)
    # P18 Decision: Deterministic Ranking
    query = query.order_by(desc(Listing.view_count), desc(Listing.created_at))
    
    # Limit
    query = query.limit(20)
    
    res = await db.execute(query)
    listings = res.scalars().all()
    
    # 6. Response
    # SEO Meta Data
    title = f"{db_city} {target_cat.slug.get('tr', 'İlanları')}"
    if p_min and p_max: title += f" {p_min}-{p_max} Fiyat Aralığı"
    elif p_min: title += f" {p_min}+ Fiyat"
    elif p_max: title += f" {p_max} Altı Fiyat"
    
    return {
        "meta": {
            "title": title,
            "description": f"{db_city} bölgesindeki en iyi {len(listings)} {target_cat.slug.get('tr')} ilanı.",
            "canonical": f"/{city}/{category}" + (f"/{price_range}" if price_range else "")
        },
        "listings": [{
            "id": str(l.id),
            "title": l.title,
            "price": l.price,
            "currency": l.currency,
            "image": l.images[0] if l.images else None
        } for l in listings]
    }
