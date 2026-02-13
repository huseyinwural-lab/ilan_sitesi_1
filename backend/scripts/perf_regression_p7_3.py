
import asyncio
import httpx
import time
import numpy as np
import os

API_URL = "http://localhost:8001/api/v2/search"

async def measure(client, name, params, count=50):
    latencies = []
    
    # Warmup
    await client.get(API_URL, params=params)
    
    for _ in range(count):
        start = time.time()
        res = await client.get(API_URL, params=params)
        dur = (time.time() - start) * 1000 # ms
        if res.status_code != 200:
            print(f"❌ {name} Failed: {res.status_code} - {res.text}")
        latencies.append(dur)
    
    p95 = np.percentile(latencies, 95)
    avg = np.mean(latencies)
    print(f"📊 {name:<30} | P95: {p95:.2f}ms | Avg: {avg:.2f}ms | Min: {min(latencies):.2f}ms")
    return p95

async def run_perf_test():
    print("🚀 Starting P7.3 Performance Regression Test (Search API v2)\n")
    
    async with httpx.AsyncClient() as client:
        # 1. Baseline: Category Browse
        p95_base = await measure(client, "Category Browse (Cars)", {"category_slug": "cars", "limit": 20})
        
        # 2. Filter: Brand (Select)
        # Note: Need a valid brand. Assuming 'bmw' or similar exists from seed.
        p95_filter = await measure(client, "Filter Brand=BMW", {"category_slug": "cars", "attrs": '{"brand":["bmw"]}', "limit": 20})
        
        # 3. Complex: Brand + Price Range
        p95_complex = await measure(client, "Complex (Brand+Price)", {
            "category_slug": "cars", 
            "attrs": '{"brand":["bmw"]}', 
            "price_min": 10000,
            "price_max": 50000,
            "limit": 20
        })
        
        # 4. Deep Pagination
        p95_page = await measure(client, "Deep Page (Page 5)", {"category_slug": "cars", "page": 5, "limit": 20})

    print("\n--- Summary ---")
    limit = 150 # ms
    success = True
    
    if p95_base > limit: 
        print(f"❌ Baseline latency too high: {p95_base:.2f}ms > {limit}ms")
        success = False
    if p95_filter > limit * 1.5: # Allow some overhead for filtering
        print(f"❌ Filter latency too high: {p95_filter:.2f}ms")
        success = False
        
    if success:
        print("✅ Performance Gate PASSED")
    else:
        print("❌ Performance Gate FAILED")

if __name__ == "__main__":
    # Install numpy if needed
    os.system("pip install numpy httpx > /dev/null 2>&1")
    asyncio.run(run_perf_test())
