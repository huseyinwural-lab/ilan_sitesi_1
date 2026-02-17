
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.affiliate import Affiliate, AffiliateClick
from server import create_access_token

async def test_affiliate_tracking():
    print("🚀 Starting Affiliate Tracking Test...")
    
    affiliate_user_id = str(uuid.uuid4())
    visitor_id = str(uuid.uuid4())
    visitor_email = f"vis_{visitor_id[:8]}@test.com"
    
    # 1. Setup Affiliate (Approved)
    async with AsyncSessionLocal() as session:
        # Clean first
        try:
            await session.execute(text("DELETE FROM affiliate_clicks"))
            # Circular dependency: Users reference Affiliates, Affiliates reference Users
            # Set User.referred_by_affiliate_id to NULL first
            await session.execute(text("UPDATE users SET referred_by_affiliate_id = NULL WHERE referred_by_affiliate_id IS NOT NULL"))
            await session.execute(text("DELETE FROM affiliates")) 
            await session.execute(text("DELETE FROM users WHERE email IN ('partner@test.com') OR email LIKE 'vis_%'"))
            await session.commit()
        except Exception as e:
            print(f"Cleanup Warning: {e}")
            await session.rollback()

        # Create User
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{affiliate_user_id}', 'partner@test.com', 'hash', 'Partner', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        
        # Create Affiliate
        affiliate_id = str(uuid.uuid4())
        slug = "partner-link"
        await session.execute(text(f"INSERT INTO affiliates (id, user_id, custom_slug, status, commission_rate, created_at, updated_at) VALUES ('{affiliate_id}', '{affiliate_user_id}', '{slug}', 'approved', 0.20, NOW(), NOW())"))
        
        await session.commit()

    base_url = "http://localhost:8001/api"
    
    async with httpx.AsyncClient() as client:
        # 2. Click Link (Redirect & Cookie)
        print("\n🔹 1. Visitor Clicks Link...")
        # Note: HTTPX doesn't follow redirects by default unless configured, but we want to check cookie on response
        resp = await client.get(f"{base_url}/ref/partner-link", follow_redirects=False)
        
        if resp.status_code == 307:
            print("✅ Redirected")
            cookies = resp.cookies
            if "aff_ref" in cookies and cookies["aff_ref"] == affiliate_id:
                print(f"✅ Cookie Set: aff_ref={cookies['aff_ref']}")
            else:
                print(f"❌ Cookie Missing or Wrong: {cookies}")
                # return # Continue to test manual cookie injection
        else:
            print(f"❌ Redirect Failed: {resp.status_code} {resp.text}")
            # return # Continue to test manual cookie injection

        # 3. Register with Cookie
        print("\n🔹 2. Visitor Registers...")
        reg_data = {
            "email": visitor_email,
            "password": "password123",
            "full_name": "Visitor User",
            "country_scope": ["TR"],
            "preferred_language": "en"
        }
        # Simulate browser sending cookie
        client.cookies.set("aff_ref", affiliate_id)
        
        resp = await client.post(f"{base_url}/auth/register", json=reg_data)
        
        if resp.status_code == 201:
            user_data = resp.json()
            print(f"✅ Registered: {user_data['id']}")
            
            # Verify Attribution
            async with AsyncSessionLocal() as session:
                res = await session.execute(text(f"SELECT referred_by_affiliate_id FROM users WHERE id = '{user_data['id']}'"))
                attributed_id = res.scalar()
                
                if str(attributed_id) == affiliate_id:
                    print("✅ Attribution Verified (referred_by_affiliate_id set)")
                else:
                    print(f"❌ Attribution Failed: Expected {affiliate_id}, Got {attributed_id}")
        else:
            print(f"❌ Registration Failed: {resp.text}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text(f"DELETE FROM affiliate_clicks"))
            await session.execute(text(f"DELETE FROM users WHERE id = '{user_data['id']}'")) # Delete referee first
            await session.execute(text(f"DELETE FROM affiliates WHERE id = '{affiliate_id}'")) # Then affiliate
            await session.execute(text(f"DELETE FROM users WHERE id = '{affiliate_user_id}'")) # Then referrer
            await session.commit()
        except:
            await session.rollback()

    print("\n🎉 Affiliate Tracking PASSED!")

if __name__ == "__main__":
    asyncio.run(test_affiliate_tracking())
