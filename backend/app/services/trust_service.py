from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.trust import UserReview
from app.models.user import User
from app.models.messaging import Conversation
from fastapi import HTTPException
import uuid

class TrustService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_review(self, reviewer_id: uuid.UUID, listing_id: uuid.UUID, rating: int, comment: str = None) -> UserReview:
        # 1. Validation: Range
        if not (1 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

        # 2. Validation: Interaction Check
        # User must have a conversation about this listing
        # And cannot review themselves (though schema allows different user IDs, let's enforce logic)
        
        # Check interaction existance
        conv = (await self.db.execute(select(Conversation).where(
            Conversation.listing_id == listing_id,
            Conversation.buyer_id == reviewer_id
        ))).scalar_one_or_none()
        
        if not conv:
            # Maybe reviewer is the seller?
            # For V1: Only Buyer can review Seller via Listing ID context usually.
            # Let's support Buyer -> Seller for now.
            raise HTTPException(status_code=400, detail="No interaction found for this listing")
            
        reviewed_user_id = conv.seller_id
        
        if reviewer_id == reviewed_user_id:
             raise HTTPException(status_code=400, detail="Cannot review yourself")

        # 3. Create Review
        review = UserReview(
            reviewer_id=reviewer_id,
            reviewed_user_id=reviewed_user_id,
            listing_id=listing_id,
            rating=rating,
            comment=comment
        )
        self.db.add(review)
        
        # 4. Update Aggregates (Denormalization)
        # Fetch current user stats
        target_user = await self.db.get(User, reviewed_user_id)
        
        # Calculate new avg (Simple iterative update)
        current_count = target_user.review_count or 0
        current_avg = target_user.rating_avg or 0.0
        
        new_count = current_count + 1
        new_avg = ((current_avg * current_count) + rating) / new_count
        
        target_user.review_count = new_count
        target_user.rating_avg = round(new_avg, 2)
        
        await self.db.commit()
        return review

    async def get_user_reviews(self, user_id: uuid.UUID, limit: int = 20) -> list:
        query = select(UserReview).where(
            UserReview.reviewed_user_id == user_id,
            UserReview.status == 'active'
        ).order_by(UserReview.created_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
