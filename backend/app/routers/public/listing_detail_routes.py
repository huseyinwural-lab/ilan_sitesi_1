from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.user import User
from app.models.dealer_profile import DealerProfile
from app.utils.slug import slugify
from app.services.analytics_service import track_interaction

router = APIRouter()

@router.get("/{listing_id}", response_model=dict)
async def get_public_listing_detail(
    listing_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        uuid_id = uuid.UUID(listing_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid ID format")

    # 1. Fetch Listing
    listing = await db.get(Listing, uuid_id)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    if listing.status == 'deleted':
        raise HTTPException(status_code=410, detail="Listing removed")
        
    if listing.status != 'active':
        # In prod, owners/admins can view non-active. For public API, hide.
        raise HTTPException(status_code=404, detail="Listing not active")

    # 2. Fetch Seller Info
    seller = await db.get(User, listing.user_id)
    
    seller_data = {
        "id": str(seller.id),
        "type": seller.user_type,
        "name": seller.full_name, # Default individual name
        "rating": getattr(seller, 'rating_avg', 0.0),
        "is_verified": getattr(seller, 'is_identity_verified', False)
    }
    
    # If Commercial, fetch Company Name
    if seller.user_type == "commercial":
        profile = (await db.execute(select(DealerProfile).where(DealerProfile.user_id == seller.id))).scalar_one_or_none()
        if profile:
            seller_data["name"] = profile.company_name

    # 3. SEO Helper
    slug = slugify(listing.title)
    
    # 4. Analytics (Async)
    # Track View
    # Note: We need request info for IP hash, passing None for now or handle in middleware
    # background_tasks.add_task(...) 
    
    return {
        "id": str(listing.id),
        "title": listing.title,
        "slug": slug,
        "price": float(listing.price) if listing.price is not None else None,
        "price_type": listing.price_type or "FIXED",
        "price_amount": float(listing.price) if listing.price is not None else None,
        "hourly_rate": float(listing.hourly_rate) if listing.hourly_rate is not None else None,
        "currency": listing.currency or "EUR",
        "description": listing.description,
        "status": listing.status,
        "published_at": listing.published_at.isoformat() if listing.published_at else None,
        "location": {
            "city": listing.city,
            "country": listing.country,
            "zip": getattr(listing, 'zip_code', None)
        },
        "media": [{"url": img, "type": "image"} for img in (listing.images or [])],
        "attributes": listing.attributes,
        "seller": seller_data,
        "contact": {
            "phone_protected": listing.contact_option_phone,
            "message_allowed": listing.contact_option_message
        }
    }
