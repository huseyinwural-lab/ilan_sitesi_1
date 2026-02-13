
import asyncio
import httpx
import time
import os

API_URL = "http://localhost:8001/api/v2/search"

async def test_cache():
    print("🚀 Starting Redis Cache Verification...")
    
    async with httpx.AsyncClient() as client:
        # 1. First Request (Cache Miss)
        print("\n1️⃣  First Request (Cold)...")
        start = time.time()
        res1 = await client.get(API_URL, params={"category_slug": "cars", "limit": 20})
        dur1 = (time.time() - start) * 1000
        print(f"   Latency: {dur1:.2f}ms")
        
        # 2. Second Request (Cache Hit)
        print("\n2️⃣  Second Request (Warm)...")
        start = time.time()
        res2 = await client.get(API_URL, params={"category_slug": "cars", "limit": 20})
        dur2 = (time.time() - start) * 1000
        print(f"   Latency: {dur2:.2f}ms")
        
        # 3. Verification
        if dur2 < 20: # Redis should be super fast
            print(f"\n✅ Cache HIT Verified! ({dur2:.2f}ms < 20ms)")
            speedup = dur1 / dur2 if dur2 > 0 else 0
            print(f"🚀 Speedup Factor: {speedup:.1f}x")
        else:
            print(f"\n⚠️ Cache Miss or Slow Redis ({dur2:.2f}ms)")

if __name__ == "__main__":
    os.system("pip install httpx > /dev/null 2>&1")
    asyncio.run(test_cache())
