from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import math
import asyncio

from app.models.analytics import UserInteraction
from app.models.moderation import Listing
from app.models.category import Category

from app.models.experimentation import ExperimentLog

from app.services.ml_serving_service import MLServingService
from app.models.ml import MLModel

class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # self.ml_service = MLServingService() # Removed: Instantiated per request with DB session

    async def log_exposure(self, user_id: str, experiment_name: str, variant: str):
        """
        Logs that a user has been exposed to an experiment variant.
        Fire-and-forget style (but awaited here for simplicity).
        """
        log = ExperimentLog(
            user_id=user_id,
            experiment_name=experiment_name,
            variant=variant,
            device_type="mobile" # Simplified for now
        )
        self.db.add(log)
        # We don't commit here to avoid slowing down the read transaction? 
        # Actually, we should commit to ensure tracking.
        # Ideally this runs in a background task.
        await self.db.commit()

    async def calculate_affinity(self, user_id: str, days: int = 30) -> Dict[str, List[str]]:
        """
        Analyzes user interactions to find top categories and cities.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Fetch interactions
        query = select(UserInteraction).where(
            UserInteraction.user_id == user_id,
            UserInteraction.created_at >= cutoff_date
        )
        result = await self.db.execute(query)
        interactions = result.scalars().all()
        
        if not interactions:
            return {"categories": [], "cities": []}

        category_scores = {}
        city_scores = {}
        
        # Weights
        weights = {
            "listing_viewed": 1,
            "listing_favorited": 5,
            "listing_contact_clicked": 10,
            "search_performed": 2
        }

        for i in interactions:
            weight = weights.get(i.event_type, 1)
            
            # Simple Time Decay (Linear for MVP)
            age_days = (datetime.now(timezone.utc) - i.created_at).days
            decay = max(0.1, 1 - (age_days / days)) # 1.0 -> 0.1
            
            score = weight * decay
            
            if i.category_id:
                cat_id = str(i.category_id)
                category_scores[cat_id] = category_scores.get(cat_id, 0) + score
                
            if i.city:
                city_key = i.city.lower().strip()
                city_scores[city_key] = city_scores.get(city_key, 0) + score

        # Sort and return Top N
        top_categories = sorted(category_scores, key=category_scores.get, reverse=True)[:3]
        top_cities = sorted(city_scores, key=city_scores.get, reverse=True)[:2]
        
        return {"categories": top_categories, "cities": top_cities}

    async def get_recommendations(
        self, 
        user_id: str, 
        country_code: str, 
        limit: int = 10,
        enable_revenue_boost: bool = True
    ) -> dict:
        """
        Hybrid Recommendation: Affinity + Popularity + Revenue Boost
        Returns: {"listings": [], "group": "A/B"}
        """
        # 1. Get User Profile
        affinity = await self.calculate_affinity(user_id)
        top_cats = affinity["categories"]
        
        recs = []
        
        # 2. Candidate Generation Query
        query = select(Listing).where(
            Listing.status == 'active',
            Listing.country == country_code
        )
        
        # Personalization Filter
        if top_cats:
            query = query.where(Listing.category_id.in_([func.uuid(c) for c in top_cats]))
            
        # 3. Ranking / Sorting Strategy
        
        # Check for Active ML Model (Stage 3 Switch)
        ml_model_query = select(MLModel).where(MLModel.is_active == True)
        ml_result = await self.db.execute(ml_model_query)
        active_model = ml_result.scalar_one_or_none()
        
        use_ml = (active_model is not None)
        
        if use_ml:
            # ML Mode: Fetch broader set, then re-rank
            query = query.limit(limit * 5) # Fetch more for re-ranking
            result = await self.db.execute(query)
            candidates = result.scalars().all()
            
            # Init ML Service with current DB session and Model Version
            ml_service = MLServingService(self.db, model_version=active_model.version)
            
            try:
                # TIMEOUT & ERROR PROTECTION
                # Python's asyncio.wait_for is used here. 
                # In prod, use a proper circuit breaker library like 'pybreaker'.
                recs = await asyncio.wait_for(ml_service.predict_ranking(user_id, candidates), timeout=0.1) # 100ms timeout
                recs = recs[:limit]
            except asyncio.TimeoutError:
                print("⚠️ ML_TIMEOUT: Fallback to Rule-Based")
                # Fallback to Rule-Based Logic (Below)
                use_ml = False
            except Exception as e:
                print(f"⚠️ ML_ERROR: {e}")
                use_ml = False
            
        if not use_ml:  # Fallback logic (Combined with existing else/elif)
            if enable_revenue_boost:
                # Rule-Based B
                query = query.order_by(
                    desc(Listing.is_showcase),
                    desc(Listing.is_premium),
                    desc(Listing.created_at),
                )
                query = query.limit(limit)
                result = await self.db.execute(query)
                recs = result.scalars().all()
            else:
                # Rule-Based A
                query = query.order_by(desc(Listing.created_at))
                query = query.limit(limit)
                result = await self.db.execute(query)
                recs = result.scalars().all()
            
        # 4. Fallback (Cold Start)
        if len(recs) < limit:
            needed = limit - len(recs)
            exclude_ids = [l.id for l in recs]
            
            fallback_query = select(Listing).where(
                Listing.status == 'active',
                Listing.country == country_code,
                Listing.id.notin_(exclude_ids)
            )
            
            if enable_revenue_boost:
                fallback_query = fallback_query.order_by(desc(Listing.is_premium), desc(Listing.view_count))
            else:
                fallback_query = fallback_query.order_by(desc(Listing.view_count))
                
            fallback_query = fallback_query.limit(needed)
            
            fb_result = await self.db.execute(fallback_query)
            recs.extend(fb_result.scalars().all())
            
        # 5. Log Exposure (Experiment Telemetry)
        if use_ml:
            exp_group = f"ML_{active_model.version}"
            await self.log_exposure(user_id, "ml_ranking_rollout", exp_group)
        else:
            exp_group = "B" if enable_revenue_boost else "A"
            await self.log_exposure(user_id, "revenue_boost_v1", exp_group)
            
        return {
            "listings": recs,
            "group": exp_group
        }
