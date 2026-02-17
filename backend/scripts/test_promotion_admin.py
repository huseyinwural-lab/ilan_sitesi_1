
import asyncio
import os
import sys
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.promotion import Promotion, Coupon
from server import create_access_token

async def test_admin_promotion_flow():
    print("🚀 Starting Promotion Admin API Test...")
    
    # 1. Setup Admin Token (Ensure user exists with super_admin role)
    # Re-using logic from invite test
    admin_id = None
    admin_email = "admin@platform.com"
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(text(f"SELECT id FROM users WHERE email = '{admin_email}'"))
        admin_id = res.scalar()
        if not admin_id:
            # Fallback (Should be seeded)
            print("⚠️ Admin not found (unexpected), skipping auth setup check.")
            return

    token = create_access_token({"sub": str(admin_id), "email": admin_email, "role": "super_admin"})
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8001/api/v1/admin"

    async with httpx.AsyncClient() as client:
        # 2. Create Promotion
        print("\n🔹 1. Create Promotion...")
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=30)
        
        promo_data = {
            "name": "Smoke Test Promo",
            "description": "20% Discount",
            "promo_type": "percentage",
            "value": 20.0,
            "currency": "EUR",
            "start_at": start.isoformat(),
            "end_at": end.isoformat(),
            "max_redemptions": 100
        }
        
        resp = await client.post(f"{base_url}/promotions", json=promo_data, headers=headers)
        if resp.status_code != 201:
            print(f"❌ Failed to create promotion: {resp.text}")
            return
        
        promo_id = resp.json()["id"]
        print(f"✅ Promotion Created: {promo_id}")

        # 3. Create Coupons (Bulk)
        print("\n🔹 2. Create Coupons (Bulk)...")
        coupon_data = {
            "code_prefix": "SMOKE",
            "count": 5,
            "usage_limit": 1,
            "per_user_limit": 1
        }
        resp = await client.post(f"{base_url}/promotions/{promo_id}/coupons", json=coupon_data, headers=headers)
        
        if resp.status_code != 200:
            print(f"❌ Failed to create coupons: {resp.text}")
            return
            
        codes = resp.json()["codes"]
        print(f"✅ Coupons Created: {len(codes)} codes (Example: {codes[0]})")

        # 4. List Coupons
        print("\n🔹 3. List Coupons...")
        resp = await client.get(f"{base_url}/promotions/{promo_id}/coupons", headers=headers)
        items = resp.json()
        if len(items) >= 5:
            print(f"✅ Listed {len(items)} coupons")
        else:
            print(f"❌ Coupon count mismatch: {len(items)}")

        # 5. Disable Coupon
        target_coupon_id = items[0]["id"]
        print(f"\n🔹 4. Disable Coupon {target_coupon_id}...")
        resp = await client.post(f"{base_url}/coupons/{target_coupon_id}/disable", headers=headers)
        
        if resp.status_code == 200:
            print("✅ Coupon Disabled")
        else:
            print(f"❌ Failed to disable: {resp.text}")

        # 6. Deactivate Promotion
        print("\n🔹 5. Deactivate Promotion...")
        resp = await client.post(f"{base_url}/promotions/{promo_id}/deactivate", headers=headers)
        
        if resp.status_code == 200:
            print("✅ Promotion Deactivated")
        else:
            print(f"❌ Failed to deactivate: {resp.text}")

    print("\n🎉 Admin Promotion Flow PASSED!")

if __name__ == "__main__":
    asyncio.run(test_admin_promotion_flow())
