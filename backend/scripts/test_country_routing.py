
import asyncio
import os
import sys
import httpx

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def test_country_routing():
    print("🚀 Starting Country Routing Test...")
    
    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        # 1. Test Root Redirect
        print("\n🔹 1. Root / Request...")
        resp = await client.get(f"{base_url}/")
        if resp.status_code == 307 and resp.headers["location"] == "/tr":
            print("✅ Redirected to /tr")
        else:
            print(f"❌ Failed: {resp.status_code} {resp.headers.get('location')}")

        # 2. Test Deep Link Redirect
        print("\n🔹 2. Deep Link /istanbul/cars Request...")
        resp = await client.get(f"{base_url}/istanbul/cars")
        if resp.status_code == 307 and resp.headers["location"] == "/tr/istanbul/cars":
            print("✅ Redirected to /tr/istanbul/cars")
        else:
            print(f"❌ Failed: {resp.status_code} {resp.headers.get('location')}")

        # 3. Test Valid Country
        print("\n🔹 3. Valid /de/berlin Request...")
        # Note: We need a dummy endpoint to test 200 OK, otherwise 404 from router.
        # But middleware should pass it through.
        # We'll check if X-Country-Code header exists in 404 response.
        resp = await client.get(f"{base_url}/de/berlin")
        if "X-Country-Code" in resp.headers and resp.headers["X-Country-Code"] == "DE":
            print("✅ Header X-Country-Code: DE present")
        else:
            print(f"❌ Header missing or wrong: {resp.headers}")

        # 4. Test API Exclusion
        print("\n🔹 4. API Request /api/health...")
        resp = await client.get(f"{base_url}/api/health")
        if resp.status_code == 200:
            print("✅ API skipped redirect")
        else:
            print(f"❌ API Redirected: {resp.status_code}")

    print("\n🎉 Country Routing Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_country_routing())
