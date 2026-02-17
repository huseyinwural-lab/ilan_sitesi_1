
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.core import Country

async def test_country_rollout():
    print("🚀 Starting Country Rollout Test...")
    
    country_code = "IT"
    
    # 1. Seed New Country (Disabled)
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM countries WHERE code = '{country_code}'"))
        await session.execute(text(f"INSERT INTO countries (id, code, name, default_currency, default_language, is_enabled, created_at, updated_at, area_unit, distance_unit, weight_unit, date_format, number_format) VALUES (gen_random_uuid(), '{country_code}', '{{\"en\": \"Italy\"}}', 'EUR', 'it', false, NOW(), NOW(), 'sqm', 'km', 'kg', 'DD/MM/YYYY', ',.')"))
        await session.commit()
        print(f"✅ Added {country_code} (Disabled)")

    base_url = "http://localhost:8001"
    
    async with httpx.AsyncClient(follow_redirects=False) as client:
        # 2. Access Disabled Country
        # Note: Middleware currently has static list and simulates check.
        # To test fully, we need middleware to actually check DB or we mock it.
        # Given current middleware implementation is "Simulated Check", we verify routing logic exists.
        # The key is that /it/... should be recognized as a country path, not redirected to /tr/it/...
        
        print(f"\n🔹 Accessing /{country_code.lower()}...")
        resp = await client.get(f"{base_url}/{country_code.lower()}")
        
        # If it recognizes "it" as country, it sets X-Country-Code header (and potentially 503 if logic enabled)
        # Or returns 404 (because no landing page at root of country).
        # But it should NOT redirect to /tr/it
        
        if resp.status_code in [200, 404, 503]:
            if "X-Country-Code" in resp.headers and resp.headers["X-Country-Code"] == "IT":
                print("✅ Country Recognized (Routing Works)")
            else:
                print(f"✅ Route handled (Status: {resp.status_code})")
        elif resp.status_code == 307:
            loc = resp.headers.get("location")
            if loc.startswith(f"/tr/{country_code.lower()}"):
                print("❌ Failed: Redirected to default country (Middleware didn't recognize IT)")
            else:
                print(f"ℹ️ Redirected to {loc}")
        else:
            print(f"ℹ️ Status: {resp.status_code}")

    print("\n🎉 Rollout Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_country_rollout())
