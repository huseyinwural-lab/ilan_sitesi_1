from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import re

from app.dependencies import get_db
from app.routers.public.search_routes import search_real_estate, SearchResponse
from app.models.moderation import Listing

router = APIRouter()

@router.get("/landing/{country}/{segment}/{transaction}/{type}/{city}", response_model=dict)
async def get_seo_landing_page(
    country: str,
    segment: str,
    transaction: str,
    type: str,
    city: str,
    page: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """
    Programmatic SEO Landing Page Endpoint.
    Translates URL path to Search Filters.
    """
    # 1. Map URL params to DB Filters
    # Transaction: satilik -> sale, kiralik -> rent
    # Type: daire -> apartment, etc. (Need a mapping dict or slug check)
    
    # Mock Mapping (In prod, fetch from Category Translation)
    # For MVP, we assume the URL slugs match our internal keys or we do simple mapping
    
    # 2. Execute Search
    # We reuse the search logic but wrap it to add SEO metadata
    # Creating a mock request context for search
    
    search_result = await search_real_estate(
        country=country,
        city=city,
        # transaction=transaction, # Not implemented in search_routes yet, but logic is there
        # type=type,
        page=page,
        db=db
    )
    
    # 3. Generate SEO Content
    count = search_result["meta"]["count"]
    min_price = "0"
    max_price = "0"
    
    # Calculate aggregates for Description (Quick DB query)
    # In prod: Cache this or use Facets
    if count > 0:
        price_stats = (await db.execute(select(func.min(Listing.price), func.max(Listing.price)).where(
            Listing.country == country.upper(),
            Listing.city.ilike(city),
            Listing.status == 'active'
        ))).one()
        min_price = f"€{price_stats[0]:,.0f}" if price_stats[0] else "0"
        max_price = f"€{price_stats[1]:,.0f}" if price_stats[1] else "0"

    title = f"{city.capitalize()} Satılık {type.capitalize()} İlanları | Platform"
    description = f"{city.capitalize()} bölgesinde {count} adet {type} ilanı. Fiyatlar {min_price} ile {max_price} arasında."
    
    return {
        "seo": {
            "title": title,
            "description": description,
            "h1": f"{city.capitalize()} {type.capitalize()} Fırsatları",
            "breadcrumbs": [
                {"label": "Anasayfa", "url": "/"},
                {"label": country.upper(), "url": f"/{country}"},
                {"label": "Emlak", "url": f"/{country}/emlak"},
                {"label": city.capitalize(), "url": f"/{country}/emlak/{segment}/{transaction}/{type}/{city}"}
            ]
        },
        "listings": search_result
    }
