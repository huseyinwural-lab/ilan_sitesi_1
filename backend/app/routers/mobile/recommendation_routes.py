from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import hashlib

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.recommendation_service import RecommendationService
from app.routers.mobile.listing_routes import MobileListingCard
from pydantic import BaseModel

router = APIRouter()

class RecommendationResponse(BaseModel):
    data: List[MobileListingCard]
    meta: dict

@router.get("/", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = 10,
    x_experiment_group: Optional[str] = Header(None, alias="X-Experiment-Group"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RecommendationService(db)
    
    country = "TR"
    if current_user.country_scope and len(current_user.country_scope) > 0:
        if "*" not in current_user.country_scope:
             country = current_user.country_scope[0]
    
    # A/B Assignment
    # 50/50 split based on User ID hash
    if x_experiment_group:
        # QA Override
        enable_boost = (x_experiment_group.upper() == "B")
    else:
        # Deterministic Hash
        user_hash = int(hashlib.md5(str(current_user.id).encode()).hexdigest(), 16)
        enable_boost = (user_hash % 2 == 0) # True = B, False = A
             
    result = await service.get_recommendations(
        user_id=current_user.id, 
        country_code=country, 
        limit=limit,
        enable_revenue_boost=enable_boost
    )
    
    listings = result["listings"]
    group = result["group"]
    
    # Map to DTO
    data = []
    for l in listings:
        data.append(MobileListingCard(
            id=str(l.id),
            title=l.title,
            price=float(l.price),
            currency=l.currency,
            image_url=l.images[0] if l.images else None,
            location=f"{l.city}, {l.country}",
            date=l.created_at.strftime("%Y-%m-%d") if l.created_at else "",
            is_premium=l.is_premium
        ))
        
    return {
        "data": data,
        "meta": {
            "experiment": "revenue_boost_v1",
            "group": group,
            "count": len(data)
        }
    }
