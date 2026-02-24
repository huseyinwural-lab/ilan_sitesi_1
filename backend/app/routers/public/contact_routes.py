from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.dependencies import get_db, get_current_user_optional
from app.models.moderation import Listing
from app.models.user import User
from app.services.analytics_service import track_interaction

router = APIRouter()

@router.get("/{listing_id}/phone", response_model=dict)
async def get_listing_phone(
    listing_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional) # Optional auth
):
    """
    Reveals the phone number and logs the interaction.
    """
    # 1. Fetch Listing & Owner
    query = select(Listing).where(Listing.id == uuid.UUID(listing_id))
    listing = (await db.execute(query)).scalar_one_or_none()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    if not listing.contact_option_phone:
        raise HTTPException(status_code=403, detail="Phone contact is disabled for this listing")
        
    owner = await db.get(User, listing.user_id)
    owner_phone = getattr(owner, "phone_number", None) if owner else None
    if not owner or not owner_phone:
        raise HTTPException(status_code=404, detail="No phone number available")

    # 2. Analytics (P21 Integration)
    # We log this as a significant event
    user_id = current_user.id if current_user else None
    
    # Fire & Forget logic (in prod use background task)
    await track_interaction(
        db=db,
        user_id=user_id,
        event_type="listing_contact_clicked",
        country_code=listing.country,
        listing_id=listing.id,
        category_id=listing.category_id,
        city=listing.city,
        meta_data={"type": "phone_reveal", "ip": request.client.host}
    )
    
    return {"phone_number": owner_phone}
