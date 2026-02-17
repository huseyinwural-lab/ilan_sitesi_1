from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.dependencies import get_db, check_permissions
from app.models.user import User
from app.models.moderation import Listing
from app.models.analytics import UserInteraction

router = APIRouter()

@router.get("/country-stats", response_model=list)
async def get_country_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin"]))
):
    """
    Returns breakdown of key metrics by country.
    """
    # 1. Listings by Country
    l_query = select(Listing.country, func.count(Listing.id)).where(Listing.status == 'active').group_by(Listing.country)
    l_res = await db.execute(l_query)
    listing_stats = {r[0]: r[1] for r in l_res.all()}
    
    # 2. Traffic by Country (Last 24h interactions)
    # Using UserInteraction country_code
    i_query = select(UserInteraction.country_code, func.count(UserInteraction.id)).group_by(UserInteraction.country_code)
    i_res = await db.execute(i_query)
    traffic_stats = {r[0]: r[1] for r in i_res.all()}
    
    # Merge
    all_countries = set(list(listing_stats.keys()) + list(traffic_stats.keys()))
    
    report = []
    for c in all_countries:
        report.append({
            "country": c,
            "active_listings": listing_stats.get(c, 0),
            "interactions": traffic_stats.get(c, 0)
        })
        
    return report
