from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid
from fastapi import HTTPException

from app.models.moderation import Listing
from app.models.user import User
from app.models.dealer_profile import DealerProfile
from app.services.quota_service import QuotaService

class ListingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_draft(self, user_id: uuid.UUID, category_id: uuid.UUID, module: str, country: str) -> Listing:
        listing = Listing(
            user_id=user_id,
            category_id=category_id,
            module=module,
            country=country,
            title="Yeni İlan", # Default title
            status="DRAFT",
            current_step=1,
            completion_percentage=10,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)
        return listing

    async def update_draft(self, listing_id: uuid.UUID, user_id: uuid.UUID, update_data: dict) -> Listing:
        listing = await self.db.get(Listing, listing_id)
        if not listing or listing.user_id != user_id:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        if listing.status not in ["DRAFT", "REJECTED", "ACTIVE"]:
             raise HTTPException(status_code=400, detail=f"Cannot edit listing in {listing.status} state")

        for k, v in update_data.items():
            if hasattr(listing, k):
                setattr(listing, k, v)
        
        listing.last_edited_at = datetime.now(timezone.utc)
        # Recalculate completion logic (Simplified)
        self._calc_completion(listing)
        
        await self.db.commit()
        await self.db.refresh(listing)
        return listing

    def _calc_completion(self, listing: Listing):
        score = 10 # Base
        if listing.title and len(listing.title) > 5: score += 20
        if listing.price: score += 10
        if listing.description: score += 20
        if listing.images and len(listing.images) > 0: score += 20
        if listing.city: score += 20
        listing.completion_percentage = min(100, score)

    async def submit_listing(self, listing_id: uuid.UUID, user_id: uuid.UUID) -> Listing:
        listing = await self.db.get(Listing, listing_id)
        if not listing or listing.user_id != user_id:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        # Completion check
        if listing.completion_percentage < 100:
             if listing.completion_percentage < 80:
                raise HTTPException(status_code=400, detail="Listing incomplete. Please fill required fields.")
        
        # Snapshot User Type
        user = await self.db.get(User, user_id)
        listing.user_type_snapshot = user.user_type
        
        # Quota Check (P10)
        quota_service = QuotaService(self.db)
        has_quota = await quota_service.check_listing_quota(user_id)
        if not has_quota:
            raise HTTPException(status_code=402, detail="Listing quota exceeded. Please upgrade your plan.")

        # EU Compliance Check (FAZ-U5)
        if user.user_type == "commercial":
            profile = (await self.db.execute(select(DealerProfile).where(DealerProfile.user_id == user.id))).scalar_one_or_none()
            if not profile or not profile.company_name or not profile.impressum_text:
                raise HTTPException(status_code=400, detail="Commercial sellers must complete Dealer Profile (Company Name & Impressum) before publishing.")

        # State Transition
        if listing.status not in ["DRAFT", "REJECTED"]:
             raise HTTPException(status_code=400, detail="Invalid transition")
             
        listing.status = "PENDING_MODERATION"
        
        await self.db.commit()
        return listing

    async def soft_delete(self, listing_id: uuid.UUID, user_id: uuid.UUID):
        listing = await self.db.get(Listing, listing_id)
        if not listing or listing.user_id != user_id:
            raise HTTPException(status_code=404, detail="Listing not found")
            
        listing.status = "DELETED"
        listing.deleted_at = datetime.now(timezone.utc)
        await self.db.commit()
