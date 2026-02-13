
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.moderation import Listing
from app.services.quota_service import QuotaService, QuotaExceededError
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/v1/listings", tags=["commercial"])
logger = logging.getLogger(__name__)

class ListingCreate(BaseModel):
    title: str
    description: str
    price: int
    currency: str = "TRY"
    category_id: str
    country: str = "TR"
    city: str
    images: list[str] = []
    attributes: Dict[str, Any] = {}
    is_showcase: bool = False

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_listing(
    data: ListingCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new listing with strict Quota Enforcement (P10).
    """
    quota_service = QuotaService(db)
    user_id = str(current_user.id)

    # 1. Quota Check & Consumption (Transactional)
    try:
        # Start strict transaction for atomicity
        async with db.begin():
            # A. Check/Consume Listing Quota
            await quota_service.consume_quota(user_id, "listing_active", 1)
            
            # B. Check/Consume Showcase Quota (if requested)
            if data.is_showcase:
                await quota_service.consume_quota(user_id, "showcase_active", 1)

            # 2. Create Listing
            # Ensure UUID conversion if string
            try:
                cat_uuid = uuid.UUID(data.category_id)
            except:
                cat_uuid = None

            listing = Listing(
                title=data.title,
                description=data.description,
                price=data.price,
                currency=data.currency,
                category_id=cat_uuid,
                country=data.country,
                city=data.city,
                user_id=current_user.id,
                status="active", # Or 'pending' if moderation is enabled
                images=data.images,
                attributes=data.attributes,
                is_showcase=data.is_showcase,
                created_at=datetime.now(timezone.utc)
            )
            db.add(listing)
            await db.flush() # Get ID
            
            logger.info(f"✅ Listing created: {listing.id} for user {user_id}. Quota consumed.")
            
            return {"id": str(listing.id), "status": listing.status}

    except QuotaExceededError as e:
        logger.warning(f"⛔ Quota Exceeded for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"❌ Create Listing Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
