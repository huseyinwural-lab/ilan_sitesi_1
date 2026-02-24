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

        # 4. GDPR Exports (30 Days)
        export_result = await db.execute(
            select(GDPRExport).where(
                GDPRExport.expires_at.isnot(None),
                GDPRExport.expires_at < now,
                GDPRExport.status != "expired",
            )
        )
        exports = export_result.scalars().all()
        export_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "exports")
        expired_count = 0
        for export in exports:
            export.status = "expired"
            export.updated_at = now
            expired_count += 1
            if export.file_path:
                path = os.path.join(export_dir, export.file_path)
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
        print(f"Expired {expired_count} GDPR exports.")

        await db.commit()
        print("✅ Cleanup Complete.")

if __name__ == "__main__":
    asyncio.run(run_retention_policy())
