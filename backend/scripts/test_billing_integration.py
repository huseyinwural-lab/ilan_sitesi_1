
import asyncio
import os
import sys
import uuid
import time
from sqlalchemy import text, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.billing import BillingCustomer, StripeSubscription, StripeEvent
from app.models.monetization import UserSubscription, SubscriptionPlan, QuotaUsage
from app.services.quota_service import QuotaService
from app.routers.billing_webhook import handle_checkout_completed

async def test_billing_flow():
    print("🚀 Starting P11 Billing Integration Test...")
    
    async with AsyncSessionLocal() as session:
        # 1. Setup User
        res = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = str(res.scalar())
        
        # Cleanup
        await session.execute(delete(UserSubscription).where(UserSubscription.user_id == user_id))
        await session.execute(delete(QuotaUsage).where(QuotaUsage.user_id == user_id))
        await session.execute(delete(StripeSubscription).where(StripeSubscription.user_id == user_id))
        await session.commit()
        
        print(f"User: {user_id}")
        qs = QuotaService(session)
        
        # 2. Check Initial Limit (Free)
        limits = await qs.get_limits(user_id)
        print(f"Initial Limits: {limits}")
        if limits['listing_active'] != 3:
            print("❌ Expected Free Limit 3")
            return

        # 3. Simulate Checkout Webhook
        print("Simulating Payment...")
        mock_session = {
            "client_reference_id": user_id,
            "subscription": "sub_mock_123",
            "metadata": {"plan_code": "TR_DEALER_PRO"},
            "expires_at": time.time() + 30*24*3600 # 30 days
        }
        
        # We need plan seeded
        plan_res = await session.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "TR_DEALER_PRO"))
        if not plan_res.scalar_one_or_none():
            print("⚠️ Plan TR_DEALER_PRO not found. Seeding...")
            session.add(SubscriptionPlan(code="TR_DEALER_PRO", name={"en":"Pro"}, price=10, currency="TRY", duration_days=30, limits={"listing": 50}))
            await session.commit()

        await handle_checkout_completed(mock_session, session)
        await session.commit()
        
        # 4. Verify Limit Upgrade
        limits_new = await qs.get_limits(user_id)
        print(f"New Limits: {limits_new}")
        
        if limits_new['listing_active'] == 50:
            print("✅ Quota Unlocked! (3 -> 50)")
        else:
            print(f"❌ Limit mismatch: {limits_new}")

if __name__ == "__main__":
    asyncio.run(test_billing_flow())
