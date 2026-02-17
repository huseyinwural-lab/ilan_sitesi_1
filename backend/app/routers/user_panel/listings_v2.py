from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
from typing import Optional, List
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.listing_service import ListingService
from app.models.moderation import Listing

router = APIRouter()

class ListingCreateDTO(BaseModel):
    category_id: str
    module: str
    country: str = "TR"

class ListingUpdateDTO(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    city: Optional[str] = None
    images: Optional[List[str]] = None

@router.post("/", response_model=dict)
async def create_draft(
    data: ListingCreateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ListingService(db)
    listing = await service.create_draft(
        current_user.id, 
        uuid.UUID(data.category_id), 
        data.module, 
        data.country
    )
    return {"id": str(listing.id), "status": listing.status, "step": listing.current_step}

@router.patch("/{listing_id}", response_model=dict)
async def update_listing(
    listing_id: str,
    data: ListingUpdateDTO,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ListingService(db)
    update_data = data.model_dump(exclude_unset=True)
    listing = await service.update_draft(uuid.UUID(listing_id), current_user.id, update_data)
    
    return {
        "id": str(listing.id), 
        "status": listing.status, 
        "completion": listing.completion_percentage,
        "last_edited": listing.last_edited_at.isoformat() if listing.last_edited_at else None
    }

@router.post("/{listing_id}/submit", response_model=dict)
async def submit_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ListingService(db)
    listing = await service.submit_listing(uuid.UUID(listing_id), current_user.id)
    return {"id": str(listing.id), "status": listing.status}

@router.delete("/{listing_id}")
async def delete_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ListingService(db)
    await service.soft_delete(uuid.UUID(listing_id), current_user.id)
    return {"message": "Listing deleted"}
