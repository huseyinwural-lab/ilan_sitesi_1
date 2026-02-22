from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.moderation import Listing
from app.schemas.user_panel import ListingDraftCreate, ListingUpdateStep1, ListingUpdateStep2, ListingUpdateStep3, ListingResponse

router = APIRouter()

@router.get("/", response_model=List[ListingResponse])
async def get_my_listings(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Listing).where(Listing.user_id == current_user.id)
    
    if status:
        query = query.where(Listing.status == status)
        
    query = query.order_by(desc(Listing.created_at))
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return [
        ListingResponse(
            id=str(l.id),
            title=l.title,
            price=float(l.price) if l.price is not None else None,
            price_type=l.price_type or "FIXED",
            price_amount=float(l.price) if l.price is not None else None,
            hourly_rate=float(l.hourly_rate) if l.hourly_rate is not None else None,
            currency=l.currency or "EUR",
            status=l.status,
            image_url=l.images[0] if l.images else None,
            view_count=l.view_count,
            created_at=l.created_at
        ) for l in listings
    ]

@router.post("/draft", response_model=ListingResponse)
async def create_draft(
    data: ListingDraftCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check limits (Mock for P28 MVP)
    # limit_service.check(current_user)
    
    listing = Listing(
        user_id=current_user.id,
        module=data.module,
        country=data.country,
        category_id=uuid.UUID(data.category_id),
        title="Yeni İlan (Taslak)",
        status="draft",
        created_at=datetime.now(timezone.utc)
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    
    return ListingResponse(
        id=str(listing.id),
        title=listing.title,
        price=0.0,
        status=listing.status,
        image_url=None,
        view_count=0,
        created_at=listing.created_at
    )

@router.put("/{listing_id}/step-1")
async def update_draft_step1(
    listing_id: str,
    data: ListingUpdateStep1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = await db.get(Listing, uuid.UUID(listing_id))
    if not listing or listing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(listing, k, v)
        
    await db.commit()
    return {"status": "updated", "step": 1}

@router.put("/{listing_id}/publish")
async def publish_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = await db.get(Listing, uuid.UUID(listing_id))
    if not listing or listing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    # Validation logic here (Price, Images, etc.)
    if not listing.price or not listing.title:
        raise HTTPException(status_code=400, detail="Missing required fields")
        
    listing.status = "pending" # Send to moderation
    await db.commit()
    return {"status": "published", "listing_status": "pending"}
