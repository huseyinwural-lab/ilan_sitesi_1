import asyncio
import sys
import os
import pandas as pd
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.ml import MLPredictionLog

async def check_drift():
    print("🚀 Starting Drift Detection Check...")
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch recent predictions (Last 24h)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        query = select(MLPredictionLog).where(MLPredictionLog.created_at >= cutoff)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        if not logs:
            print("⚠️ No prediction logs found in last 24h. Skipping check.")
            return

        df = pd.DataFrame([{
            'score': log.top_score,
            'latency': log.execution_time_ms,
            'version': log.model_version
        } for log in logs])
        
        # 2. Score Drift (Mean Score check)
        mean_score = df['score'].mean()
        print(f"📊 Mean Prediction Score: {mean_score:.4f}")
        
        if mean_score < 0.05: # Threshold dependent on model calibration
            print("🚨 ALERT: Model is predicting very low scores. Potential drift or bug.")
            
        # 3. Latency Check
        p95_latency = df['latency'].quantile(0.95)
        print(f"⏱️ P95 Latency: {p95_latency:.2f}ms")
        
        if p95_latency > 200:
            print("🚨 ALERT: Latency exceeded 200ms budget.")
            
        print("✅ Drift Check Complete.")

if __name__ == "__main__":
    asyncio.run(check_drift())
