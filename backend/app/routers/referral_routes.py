
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.dependencies import get_db
from app.models.user import User
from app.models.referral_tier import ReferralTier
from app.core.redis_cache import cache_service
from typing import List, Optional
import json

router = APIRouter(prefix="/v1/referral", tags=["referral"])

@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Public Leaderboard (Cached 10 mins).
    """
    cache_key = f"leaderboard:top:{limit}"
    
    # 1. Try Cache
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return cached_data
        
    # 2. Query DB
    # Join with Tier for badge info
    stmt = (
        select(User, ReferralTier)
        .outerjoin(ReferralTier, User.referral_tier_id == ReferralTier.id)
        .where(User.referral_count_confirmed > 0)
        .order_by(desc(User.referral_count_confirmed), User.created_at.asc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    leaderboard = []
    for idx, (user, tier) in enumerate(rows):
        # Mask Name: "John Doe" -> "John D."
        name_parts = user.full_name.split()
        masked_name = user.full_name
        if len(name_parts) > 1:
            masked_name = f"{name_parts[0]} {name_parts[-1][0]}."
            
        leaderboard.append({
            "rank": idx + 1,
            "name": masked_name,
            "count": user.referral_count_confirmed,
            "tier": tier.name if tier else "Standard",
            "badge": tier.badge_icon if tier else None
        })
        
    # 3. Set Cache
    await cache_service.set(cache_key, leaderboard, ttl=600) # 10 mins
    
    return leaderboard
