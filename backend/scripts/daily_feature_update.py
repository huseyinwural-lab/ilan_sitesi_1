import asyncio
import sys
import os
from sqlalchemy import select, delete
from datetime import datetime, timezone, timedelta
from app.database import AsyncSessionLocal
from app.models.analytics import UserInteraction, UserFeature
from app.models.user import User

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def aggregate_features():
    print(f"🚀 Starting Feature Aggregation Job at {datetime.now(timezone.utc)}")
    
    async with AsyncSessionLocal() as db:
        # 1. Get all active users (users with interactions in last 30 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        
        # In a real big-data scenario, we would stream this or use Spark/Dask.
        # For MVP, we iterate active users.
        query = select(UserInteraction.user_id).where(
            UserInteraction.created_at >= cutoff,
            UserInteraction.user_id.isnot(None)
        ).distinct()
        
        result = await db.execute(query)
        user_ids = result.scalars().all()
        print(f"found {len(user_ids)} active users to process.")
        
        for user_id in user_ids:
            # 2. Fetch interactions for user
            i_query = select(UserInteraction).where(
                UserInteraction.user_id == user_id,
                UserInteraction.created_at >= cutoff
            )
            i_result = await db.execute(i_query)
            interactions = i_result.scalars().all()
            
            cat_scores = {}
            city_scores = {}
            total_activity = 0
            
            weights = {
                "listing_viewed": 1,
                "listing_favorited": 5,
                "listing_contact_clicked": 10
            }
            
            for i in interactions:
                weight = weights.get(i.event_type, 1)
                
                # Decay
                age = (datetime.now(timezone.utc) - i.created_at).days
                decay = max(0.1, 1 - (age / 30))
                
                score = weight * decay
                total_activity += score
                
                if i.category_id:
                    cid = str(i.category_id)
                    cat_scores[cid] = cat_scores.get(cid, 0) + score
                    
                if i.city:
                    city = i.city.lower().strip()
                    city_scores[city] = city_scores.get(city, 0) + score
            
            # Normalize scores (Optional, but good for ML)
            # For now, store raw weighted scores
            
            # 3. Upsert into UserFeature
            # Check existing
            f_query = select(UserFeature).where(UserFeature.user_id == user_id)
            f_result = await db.execute(f_query)
            feature = f_result.scalar_one_or_none()
            
            if not feature:
                feature = UserFeature(user_id=user_id)
                db.add(feature)
            
            feature.category_affinity = cat_scores
            feature.city_affinity = city_scores
            feature.activity_score = min(10.0, total_activity / 10.0) # Cap at 10 roughly
            feature.last_updated_at = datetime.now(timezone.utc)
            
        await db.commit()
        print("✅ Feature Aggregation Complete.")

if __name__ == "__main__":
    asyncio.run(aggregate_features())
