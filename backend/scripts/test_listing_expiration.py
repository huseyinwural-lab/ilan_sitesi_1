
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text, select
from datetime import datetime, timedelta, timezone
from jose import jwt

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.user import User
from app.services.quota_service import QuotaService
from app.models.category import Category
from app.models.vehicle_mdm import VehicleMake, VehicleModel

# Mock token generator
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-change-in-production-2024")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def test_full_expiration_lifecycle():
    print("🚀 Starting P13 Full Lifecycle Test (Expiration & Renew)...")
    
    user_id = None
    listing_id = None
    category_id = None
    
    # 1. Setup
    async with AsyncSessionLocal() as session:
        # User
        email = f"test_lifecycle_{uuid.uuid4().hex[:8]}@example.com"
        
        # Cleanup potential collision (paranoid)
        await session.execute(text(f"DELETE FROM users WHERE email = '{email}'"))
        await session.commit()

        user = User(
            email=email,
            hashed_password='hash',
            full_name='Lifecycle Tester',
            role='individual',
            country_scope=[],
            preferred_language='en',
            is_active=True,
            is_verified=True,
            two_factor_enabled=False
        )
        session.add(user)
        await session.flush()
        user_id = user.id
        
        # Category
        cat_res = await session.execute(select(Category).limit(1))
        category = cat_res.scalar_one()
        category_id = category.id
        
        # Quota Setup (Give usage to start with)
        # We will create an ACTIVE listing that is about to expire.
        # This listing consumes 1 quota.
        qs = QuotaService(session)
        await qs.consume_quota(str(user_id), "listing_active", 1)
        
        now = datetime.now(timezone.utc)
        listing = Listing(
            title="Lifecycle Test Listing",
            user_id=user_id,
            status="active",
            created_at=now - timedelta(days=90),
            expires_at=now - timedelta(seconds=1), # Expired!
            price=100, currency="TRY", country="TR", module="vehicle", category_id=category_id
        )
        session.add(listing)
        await session.commit()
        listing_id = listing.id
        
        print(f"✅ Setup Complete. User: {user_id}, Listing: {listing_id}")
        
    # 2. Run Expiration Job
    print("\n⏳ Running Expiration Job...")
    from scripts.process_expirations import process_expirations
    await process_expirations()
    
    # 3. Verify Expiration
    async with AsyncSessionLocal() as session:
        qs = QuotaService(session)
        usage = await qs.get_usage(str(user_id), "listing_active")
        
        res = await session.execute(select(Listing).where(Listing.id == listing_id))
        listing = res.scalar_one()
        
        print(f"   Status: {listing.status}")
        print(f"   Quota: {usage}")
        
        if listing.status == 'expired' and usage == 0:
            print("✅ Expiration Verified (Status expired, Quota released)")
        else:
            print(f"❌ Expiration Failed! Status: {listing.status}, Quota: {usage}")
            return

    # 4. Test Renew (Expired -> Active)
    print("\n🔄 Testing Renew (Expired -> Active)...")
    token = create_access_token({"sub": str(user_id), "email": email, "role": "individual"})
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        url = f"http://localhost:8001/api/v2/listings/{listing_id}/renew"
        resp = await client.post(url, headers=headers)
        
        if resp.status_code == 200:
            print("   API Call: Success")
        else:
            print(f"   API Call Failed: {resp.text}")
            return

    async with AsyncSessionLocal() as session:
        qs = QuotaService(session)
        usage = await qs.get_usage(str(user_id), "listing_active")
        res = await session.execute(select(Listing).where(Listing.id == listing_id))
        listing = res.scalar_one()
        
        if listing.status == 'active' and usage == 1:
            print("✅ Renew Verified (Status active, Quota consumed)")
        else:
            print(f"❌ Renew Failed! Status: {listing.status}, Quota: {usage}")
            return

    # 5. Test Renew Again (Active -> Active)
    print("\n🔄 Testing Renew (Active -> Active)...")
    async with httpx.AsyncClient() as client:
        url = f"http://localhost:8001/api/v2/listings/{listing_id}/renew"
        resp = await client.post(url, headers=headers)
        
        if resp.status_code == 200:
            print("   API Call: Success")
        else:
            print(f"   API Call Failed: {resp.text}")
            return

    async with AsyncSessionLocal() as session:
        qs = QuotaService(session)
        usage = await qs.get_usage(str(user_id), "listing_active")
        
        if usage == 1:
            print("✅ Active Renew Verified (Quota maintained at 1)")
        else:
            print(f"❌ Active Renew Failed! Quota: {usage}")
            return

    print("\n🎉 Full Lifecycle Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_full_expiration_lifecycle())
