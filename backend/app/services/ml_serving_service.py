import random
import time
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ml import MLPredictionLog

class FairnessReRanker:
    @staticmethod
    def rerank(candidates: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Enforces business logic constraints on the raw ML list.
        Constraint 1: Max 1 Sponsored (Premium/Showcase) per 3 items.
        """
        organic = []
        sponsored = []
        
        for c in candidates:
            # Check attribute directly or via dict
            is_prem = getattr(c, 'is_premium', False) or getattr(c, 'is_showcase', False)
            if is_prem:
                sponsored.append(c)
            else:
                organic.append(c)
                
        final_list = []
        
        # Interleaving Strategy
        while len(final_list) < limit:
            if not organic and not sponsored:
                break
                
            # Slots 1, 2: Organic
            if len(final_list) % 3 != 2: 
                if organic:
                    final_list.append(organic.pop(0))
                elif sponsored:
                    final_list.append(sponsored.pop(0))
            # Slot 3: Sponsored
            else:
                if sponsored:
                    final_list.append(sponsored.pop(0))
                elif organic:
                    final_list.append(organic.pop(0))
                    
        return final_list

class MLServingService:
    """
    Mock ML Serving Service with Fairness and Logging.
    """
    
    def __init__(self, db: AsyncSession, model_path: str = None, model_version: str = "v1-mock"):
        self.db = db
        self.model_path = model_path
        self.model_version = model_version

    async def predict_ranking(self, user_id: str, candidates: List[Dict]) -> List[Dict]:
        """
        Re-ranks candidates based on score AND fairness.
        Logs prediction stats.
        """
        start_time = time.time()
        
        # 1. Scoring (Simulated Revenue-Aware Score)
        scored_candidates = []
        max_score = 0.0
        
        for c in candidates:
            base_score = random.random()
            
            # Revenue Boost in Scoring (Objective Function Simulation)
            if getattr(c, 'is_premium', False):
                base_score += 0.3 # Higher p(conversion) assumption
            
            if base_score > max_score:
                max_score = base_score
                
            scored_candidates.append((base_score, c))
            
        # Sort DESC
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        raw_ranked = [x[1] for x in scored_candidates]
        
        # 2. Fairness Re-Ranking
        final_ranked = FairnessReRanker.rerank(raw_ranked, limit=len(raw_ranked))
        
        execution_time = (time.time() - start_time) * 1000
        
        # 3. Async Logging (Fire & Forget typically, but awaited for MVP)
        await self.log_prediction(user_id, len(candidates), max_score, execution_time)
        
        return final_ranked

    async def log_prediction(self, user_id, count, top_score, exec_time):
        try:
            log = MLPredictionLog(
                model_version=self.model_version,
                user_id=user_id,
                candidate_count=count,
                top_score=top_score,
                execution_time_ms=exec_time
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            print(f"ML_LOG_ERROR: {e}") # Non-blocking error
