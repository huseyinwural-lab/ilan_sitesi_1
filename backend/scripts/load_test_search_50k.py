
import asyncio
import httpx
import time
import numpy as np
import os

API_URL = "http://localhost:8001/api/v2/search"

# Concurrency Config
CONCURRENT_USERS = 50
TOTAL_REQUESTS = 1000

async def user_session(client, scenarios):
    latencies = []
    for _ in range(TOTAL_REQUESTS // CONCURRENT_USERS):
        scenario = random.choice(scenarios)
        start = time.time()
        try:
            res = await client.get(API_URL, params=scenario['params'])
            dur = (time.time() - start) * 1000
            if res.status_code == 200:
                latencies.append(dur)
            else:
                print(f"Error {res.status_code}: {res.text[:100]}")
        except Exception as e:
            print(f"Request Error: {e}")
    return latencies

import random

async def run_load_test():
    print(f"🚀 Starting 50K Search Load Test (Users: {CONCURRENT_USERS}, Total Req: {TOTAL_REQUESTS})...")
    
    scenarios = [
        {"name": "Category Browse", "params": {"category_slug": "cars", "limit": 20}, "weight": 0.5},
        {"name": "Filter: Brand", "params": {"category_slug": "cars", "attrs": '{"brand":["bmw"]}', "limit": 20}, "weight": 0.3},
        {"name": "Complex Filter", "params": {"category_slug": "cars", "price_min": 50000, "price_max": 200000, "attrs": '{"fuel_type":["diesel"]}'}, "weight": 0.1},
        {"name": "Text Search", "params": {"q": "sahibinden", "limit": 20}, "weight": 0.1}
    ]
    
    # Weighted list
    weighted_scenarios = []
    for s in scenarios:
        weighted_scenarios.extend([s] * int(s['weight'] * 10))

    start_time = time.time()
    
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=CONCURRENT_USERS)) as client:
        tasks = [user_session(client, weighted_scenarios) for _ in range(CONCURRENT_USERS)]
        results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    all_latencies = [l for sub in results for l in sub]
    
    print("\n--- Results ---")
    print(f"Total Requests: {len(all_latencies)}")
    print(f"Duration: {total_time:.2f}s")
    print(f"RPS: {len(all_latencies) / total_time:.2f}")
    print(f"P50: {np.percentile(all_latencies, 50):.2f}ms")
    print(f"P95: {np.percentile(all_latencies, 95):.2f}ms")
    print(f"P99: {np.percentile(all_latencies, 99):.2f}ms")
    
    limit = 150
    p95 = np.percentile(all_latencies, 95)
    if p95 < limit:
        print(f"✅ PASSED (P95 {p95:.2f}ms < {limit}ms)")
    else:
        print(f"❌ FAILED (P95 {p95:.2f}ms > {limit}ms)")

if __name__ == "__main__":
    os.system("pip install numpy httpx > /dev/null 2>&1")
    asyncio.run(run_load_test())
