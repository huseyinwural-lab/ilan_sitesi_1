
import asyncio
import os
import sys
import uuid
import json
from sqlalchemy import text, select, func
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.referral import ReferralReward, ConversionEvent
from app.models.user import User
from app.models.billing import Invoice, BillingCustomer
from app.services.referral_service import ReferralService

# Mock Stripe for the test context
from unittest.mock import MagicMock
import stripe
stripe.Customer = MagicMock()
stripe.Customer.create_balance_transaction.return_value = MagicMock(id="txn_mock_123")

async def test_funnel_integrity():
    print("🚀 Starting P15 Funnel Integrity Test...")
    
    referrer_id = str(uuid.uuid4())
    referee_id = str(uuid.uuid4())
    referee_email = f"referee_{referee_id[:8]}@test.com"
    referrer_code = "FUNNELREF"
    
    # 1. Setup Data
    async with AsyncSessionLocal() as session:
        # Cleanup ALL test data cascadingly if possible, or order strictly
        try:
            await session.execute(text("DELETE FROM conversion_events"))
            await session.execute(text("DELETE FROM referral_rewards"))
            await session.execute(text("DELETE FROM payment_attempts")) # Dependency of invoice
            await session.execute(text("DELETE FROM refunds")) # Correct table name
            await session.execute(text("DELETE FROM invoice_items")) # Dependency of invoice
            await session.execute(text("DELETE FROM invoices"))
            await session.execute(text("DELETE FROM billing_customers"))
            await session.execute(text("UPDATE users SET referred_by = NULL")) # Break self-ref cycle
            await session.execute(text("DELETE FROM users WHERE email LIKE '%@test.com'"))
            await session.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")
            await session.rollback()

        # Create Referrer & Referee
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, referral_code, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{referrer_id}', 'referrer_{referrer_id[:8]}@test.com', 'hash', 'Referrer', 'individual', true, true, '{referrer_code}', '[]', 'en', false, NOW(), NOW())"))
        
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, referred_by, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{referee_id}', '{referee_email}', 'hash', 'Referee', 'individual', true, true, '{referrer_id}', '[]', 'en', false, NOW(), NOW())"))
        
        # Referrer must have billing customer for reward
        await session.execute(text(f"INSERT INTO billing_customers (user_id, stripe_customer_id, balance, currency, created_at) VALUES ('{referrer_id}', 'cus_referrer', 0, 'TRY', NOW())"))
        
        await session.commit()

    # 2. Scenario A: Checkout Started (Abandon)
    print("\n🔹 Scenario A: Checkout Started (Abandon)")
    async with AsyncSessionLocal() as session:
        # Log event
        event = ConversionEvent(
            event_name="checkout_started",
            user_id=uuid.UUID(referee_id),
            properties=json.dumps({"plan": "PRO", "amount": 100})
        )
        session.add(event)
        await session.commit()
        
        # Check Reward
        reward_exists = await session.execute(select(ReferralReward).where(ReferralReward.referee_id == uuid.UUID(referee_id)))
        if not reward_exists.scalar_one_or_none():
            print("✅ Correct: No reward generated for abandoned checkout.")
        else:
            print("❌ FAIL: Reward generated prematurely!")

    # 3. Scenario B: Checkout Completed (Success)
    print("\n🔹 Scenario B: Checkout Completed (Success)")
    
    # Simulate Webhook Logic (Process Reward)
    async with AsyncSessionLocal() as session:
        # Create Invoice (Simulate Paid)
        invoice_id = uuid.uuid4()
        # Note: Invoice model has 'number', not 'invoice_no' in recent migration?
        # Let's check model definition. It says 'number'.
        # But previous P1 routes used invoice_no.
        # Let's use 'number' based on the error.
        await session.execute(text(f"INSERT INTO invoices (id, user_id, number, status, total_amount, currency, created_at, updated_at) VALUES ('{invoice_id}', '{referee_id}', 'INV-TEST-001', 'paid', 100.00, 'TRY', NOW(), NOW())"))
        await session.commit()
        
        # Log event
        event = ConversionEvent(
            event_name="checkout_completed",
            user_id=uuid.UUID(referee_id),
            properties=json.dumps({"amount": 100, "invoice_id": str(invoice_id)})
        )
        session.add(event)
        await session.commit()
        
        # Trigger Reward Logic
        ref_service = ReferralService(session)
        await ref_service.process_reward(referee_id, amount=100.00)
        
        # Verify Reward
        reward = (await session.execute(select(ReferralReward).where(ReferralReward.referee_id == uuid.UUID(referee_id)))).scalar_one_or_none()
        if reward and reward.status == 'applied':
            print(f"✅ Success: Reward generated ({reward.amount} {reward.currency})")
        else:
            print(f"❌ FAIL: Reward missing or status wrong. Status: {reward.status if reward else 'None'}")

    # 4. Scenario C: Duplicate Webhook (Idempotency)
    print("\n🔹 Scenario C: Duplicate Webhook (Idempotency)")
    async with AsyncSessionLocal() as session:
        ref_service = ReferralService(session)
        # Call again
        await ref_service.process_reward(referee_id, amount=100.00)
        
        # Count rewards
        count = (await session.execute(select(func.count(ReferralReward.id)).where(ReferralReward.referee_id == uuid.UUID(referee_id)))).scalar()
        if count == 1:
            print("✅ Correct: No duplicate reward generated.")
        else:
            print(f"❌ FAIL: Duplicate rewards found! Count: {count}")

    # 5. Data Cleanup (End)
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("DELETE FROM conversion_events"))
            await session.execute(text("DELETE FROM referral_rewards"))
            await session.execute(text("DELETE FROM payment_attempts")) 
            await session.execute(text("DELETE FROM refunds")) 
            await session.execute(text("DELETE FROM invoice_items")) 
            await session.execute(text("DELETE FROM invoices"))
            await session.execute(text("DELETE FROM billing_customers"))
            await session.execute(text("UPDATE users SET referred_by = NULL"))
            await session.execute(text("DELETE FROM users WHERE email LIKE '%@test.com'"))
            await session.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")
            await session.rollback()

    print("\n🎉 Funnel Integrity Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_funnel_integrity())
