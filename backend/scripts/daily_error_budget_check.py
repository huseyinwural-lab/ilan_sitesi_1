import asyncio
import sys
import os
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.ml import MLPredictionLog

async def check_error_budget():
    print("📉 Daily Error Budget & Health Check...")
    
    async with AsyncSessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        # 1. ML Latency Check
        # We define "Failure" here as Latency > 200ms (Soft Failure) or actual Exceptions (not logged here yet)
        
        query = select(MLPredictionLog).where(MLPredictionLog.created_at >= cutoff)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        total_reqs = len(logs)
        if total_reqs == 0:
            print("✅ No traffic today. Error Budget: 100% Remaining.")
            return

        slow_reqs = sum(1 for log in logs if log.execution_time_ms > 200)
        failure_rate = (slow_reqs / total_reqs) * 100
        
        print(f"📊 Traffic: {total_reqs} requests")
        print(f"🐢 Slow Requests (>200ms): {slow_reqs}")
        print(f"⚠️ 'Performance Error' Rate: {failure_rate:.2f}%")
        
        # Threshold: 5%
        if failure_rate > 5.0:
            print("❌ CRITICAL: Error Budget Depleted! High Latency Detected.")
            # Trigger Alert Logic (Slack/PagerDuty) would go here
        else:
            print("✅ Status: Healthy (Within Error Budget)")

if __name__ == "__main__":
    asyncio.run(check_error_budget())
