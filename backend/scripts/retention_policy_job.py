import asyncio
import sys
import os
from sqlalchemy import delete, select
from datetime import datetime, timedelta, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.analytics import UserInteraction
from app.models.experimentation import ExperimentLog
from app.models.ml import MLPredictionLog
from app.models.gdpr_export import GDPRExport

async def run_retention_policy():
    print("🧹 Starting Retention Policy Job...")
    
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        
        # 1. ML Logs (30 Days)
        cutoff_ml = now - timedelta(days=30)
        res = await db.execute(delete(MLPredictionLog).where(MLPredictionLog.created_at < cutoff_ml))
        print(f"Deleted {res.rowcount} old ML logs.")
        
        # 2. Experiment Logs (90 Days)
        cutoff_exp = now - timedelta(days=90)
        res = await db.execute(delete(ExperimentLog).where(ExperimentLog.created_at < cutoff_exp))
        print(f"Deleted {res.rowcount} old Experiment logs.")
        
        # 3. Interactions (365 Days)
        cutoff_int = now - timedelta(days=365)
        res = await db.execute(delete(UserInteraction).where(UserInteraction.created_at < cutoff_int))
        print(f"Deleted {res.rowcount} old User Interactions.")
        
        await db.commit()
        print("✅ Cleanup Complete.")

if __name__ == "__main__":
    asyncio.run(run_retention_policy())
