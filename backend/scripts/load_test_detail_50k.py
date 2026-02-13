
import asyncio
import httpx
import time
import numpy as np
import os
import random
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

API_URL = "http://localhost:8001/api/v2/listings"

# Concurrency
CONCURRENT_USERS = 5
TOTAL_REQUESTS = 50

async def get_test_ids(limit=100):
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id FROM listings WHERE status = 'active' ORDER BY random() LIMIT :limit"), {"limit": limit})
        return [str(r[0]) for r in res.fetchall()]

async def user_session(client, ids):
    latencies = []
    for _ in range(TOTAL_REQUESTS // CONCURRENT_USERS):
        target_id = random.choice(ids)
        start = time.time()
        try:
            res = await client.get(f"{API_URL}/{target_id}", timeout=10.0)
            dur = (time.time() - start) * 1000
            if res.status_code == 200:
                latencies.append(dur)
            else:
                print(f"Error {res.status_code}")
        except Exception as e:
            print(f"Request Error: {e}")
    return latencies

async def run_load_test():
    print(f"🚀 Starting 50K Detail Page Load Test...")
    
    ids = await get_test_ids()
    if not ids:
        print("❌ No listings found.")
        return

    start_time = time.time()
    
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENT_USERS)) as client:
        tasks = [user_session(client, ids) for _ in range(CONCURRENT_USERS)]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    all_latencies = [l for sub in results for l in sub]
    
    print("\n--- Results ---")
    print(f"Total Requests: {len(all_latencies)}")
    print(f"Duration: {total_time:.2f}s")
    print(f"RPS: {len(all_latencies) / total_time:.2f}")
    print(f"P50: {np.percentile(all_latencies, 50):.2f}ms")
    print(f"P95: {np.percentile(all_latencies, 95):.2f}ms")
    
    limit = 120
    p95 = np.percentile(all_latencies, 95)
    if p95 < limit:
        print(f"✅ PASSED (P95 {p95:.2f}ms < {limit}ms)")
    else:
        print(f"❌ FAILED (P95 {p95:.2f}ms > {limit}ms)")

if __name__ == "__main__":
    os.system("pip install numpy httpx > /dev/null 2>&1")
    asyncio.run(run_load_test())
