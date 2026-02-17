import asyncio
import sys
import os
import time
import httpx
import statistics
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

from app.database import AsyncSessionLocal
from app.models.ml import MLPredictionLog

async def run_audit():
    print("🕵️ Starting P25 Performance Audit...")
    
    # 1. Analyze ML Logs (Backend Latency History)
    async with AsyncSessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        query = select(MLPredictionLog).where(MLPredictionLog.created_at >= cutoff)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        print("\n--- ML Inference Latency (Last 24h) ---")
        if logs:
            times = [l.execution_time_ms for l in logs]
            print(f"Count: {len(times)}")
            print(f"P50: {statistics.median(times):.2f}ms")
            print(f"P95: {sorted(times)[int(len(times)*0.95)]:.2f}ms")
        else:
            print("No ML logs found.")

    # 2. Active Probe (Live API Latency)
    print("\n--- Active API Probe (Search) ---")
    url = "http://localhost:8001/api/v1/search/real-estate?country=DE&city=Berlin"
    latencies = []
    
    async with httpx.AsyncClient() as client:
        # Warmup
        await client.get(url)
        
        # Measure 10 requests
        for i in range(10):
            start = time.time()
            resp = await client.get(url)
            elapsed = (time.time() - start) * 1000
            latencies.append(elapsed)
            if resp.status_code != 200:
                print(f"❌ Request failed: {resp.status_code}")
                
    if latencies:
        print(f"P50: {statistics.median(latencies):.2f}ms")
        print(f"P95: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}ms")
        print(f"Min: {min(latencies):.2f}ms")
        print(f"Max: {max(latencies):.2f}ms")
        
        if statistics.median(latencies) > 500:
            print("⚠️ WARNING: Search Latency is High!")
        else:
            print("✅ Status: Healthy")

if __name__ == "__main__":
    asyncio.run(run_audit())
