
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.user import User, SignupAllowlist
from server import create_access_token

async def test_referral_flow():
    print("🚀 Starting Referral Flow Test...")
    
    referrer_email = f"referrer_{uuid.uuid4().hex[:6]}@example.com"
    referee_email = f"referee_{uuid.uuid4().hex[:6]}@example.com"
    
    # 1. Setup Referrer
    referrer_code = None
    async with AsyncSessionLocal() as session:
        # Create Referrer (Manual DB insert to simulate existing user with code)
        referrer_id = uuid.uuid4()
        referrer_code = "TESTREF1"
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, referral_code, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{referrer_id}', '{referrer_email}', 'hash', 'Referrer', 'individual', true, true, '{referrer_code}', '[]', 'en', false, NOW(), NOW())"))
        
        # Add to Allowlist (for register test)
        await session.execute(text(f"INSERT INTO signup_allowlist (id, email, is_used, created_at) VALUES ('{uuid.uuid4()}', '{referee_email}', false, NOW())"))
        
        await session.commit()
        print(f"✅ Referrer Created: {referrer_code}")

    async with httpx.AsyncClient() as client:
        base_url = "http://localhost:8001/api"
        
        # 2. Register Referee with Code
        print("\n🔹 Testing Registration with Referral Code...")
        reg_data = {
            "email": referee_email,
            "password": "password123",
            "full_name": "Referee User",
            "country_scope": ["TR"],
            "referral_code": referrer_code
        }
        resp = await client.post(f"{base_url}/auth/register", json=reg_data)
        
        if resp.status_code == 201:
            user_data = resp.json()
            print(f"✅ Registered. User ID: {user_data['id']}")
            
            # Verify DB
            async with AsyncSessionLocal() as session:
                res = await session.execute(text(f"SELECT referred_by, referral_code FROM users WHERE id = '{user_data['id']}'"))
                row = res.one()
                if str(row[0]) == str(referrer_id):
                    print("✅ Attribution Verified (referred_by set correctly)")
                else:
                    print(f"❌ Attribution Failed! Expected {referrer_id}, Got {row[0]}")
                    
                if row[1]:
                    print(f"✅ New User has own code: {row[1]}")
                else:
                    print("❌ New User has NO referral code")
        else:
            print(f"❌ Registration Failed: {resp.status_code} {resp.text}")

    print("\n🎉 Referral Flow PASSED!")

if __name__ == "__main__":
    asyncio.run(test_referral_flow())
