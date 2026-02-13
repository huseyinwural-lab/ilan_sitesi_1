
import asyncio
import httpx
import time
import numpy as np
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

API_URL = "http://localhost:8001/api/v2/listings"

async def get_test_id():
    async with AsyncSessionLocal() as session:
        # Get a random active listing ID
        res = await session.execute(text("SELECT id FROM listings WHERE status = 'active' LIMIT 1"))
        row = res.fetchone()
        return str(row[0]) if row else None

async def measure(client, url, name, count=50):
    latencies = []
    
    # Warmup
    await client.get(url)
    
    for _ in range(count):
        start = time.time()
        res = await client.get(url)
        dur = (time.time() - start) * 1000 # ms
        if res.status_code != 200:
            print(f"❌ {name} Failed: {res.status_code}")
        latencies.append(dur)
    
    p95 = np.percentile(latencies, 95)
    avg = np.mean(latencies)
    print(f"📊 {name:<30} | P95: {p95:.2f}ms | Avg: {avg:.2f}ms | Min: {min(latencies):.2f}ms")
    return p95

async def run_perf_test():
    print("🚀 Starting P8 Detail Page Performance Regression Test\n")
    
    listing_id = await get_test_id()
    if not listing_id:
        print("❌ No active listings found to test.")
        return

    target_url = f"{API_URL}/{listing_id}"
    print(f"Target: {target_url}")

    async with httpx.AsyncClient() as client:
        # 1. Detail API (Full aggregation: Listing + User + Attributes + Related)
        p95 = await measure(client, target_url, "Detail API (Aggregation)")
        
    print("\n--- Summary ---")
    limit = 100 # ms target
    if p95 < limit:
        print(f"✅ Performance Gate PASSED ({p95:.2f}ms < {limit}ms)")
    else:
        print(f"⚠️ Performance Warning ({p95:.2f}ms > {limit}ms)")

if __name__ == "__main__":
    os.system("pip install numpy httpx > /dev/null 2>&1")
    asyncio.run(run_perf_test())
