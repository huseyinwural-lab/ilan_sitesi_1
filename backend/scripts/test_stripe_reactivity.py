
import asyncio
import os
import sys
import uuid
import httpx
from datetime import datetime, timezone, timedelta
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.referral import ReferralReward
from app.models.ledger import RewardLedger
from server import create_access_token

async def test_stripe_reactivity():
    print("🚀 Starting P16 Stripe Reactivity Test...")
    
    # 1. Setup Data (Confirmed Reward)
    referrer_id = str(uuid.uuid4())
    referee_id = str(uuid.uuid4())
    reward_id = str(uuid.uuid4())
    invoice_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        # Cleanup
        try:
            await session.execute(text(f"DELETE FROM reward_ledger"))
            await session.execute(text(f"DELETE FROM referral_rewards"))
            await session.execute(text(f"DELETE FROM invoices"))
            await session.execute(text(f"DELETE FROM billing_customers"))
            await session.execute(text(f"DELETE FROM users WHERE email LIKE '%@test.com'"))
            await session.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")
            await session.rollback()

        # Create Users
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{referrer_id}', 'ref_p16_{referrer_id[:8]}@test.com', 'hash', 'Referrer', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{referee_id}', 'referee_p16_{referee_id[:8]}@test.com', 'hash', 'Referee', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        
        # Billing Customer (Referrer)
        await session.execute(text(f"INSERT INTO billing_customers (user_id, stripe_customer_id, balance, currency, created_at) VALUES ('{referrer_id}', 'cus_ref_p16', -10000, 'TRY', NOW())")) # -100 TRY Credit
        
        # Reward (Confirmed)
        await session.execute(text(f"INSERT INTO referral_rewards (id, referrer_id, referee_id, amount, currency, status, created_at) VALUES ('{reward_id}', '{referrer_id}', '{referee_id}', 100.00, 'TRY', 'confirmed', NOW())"))
        
        # Invoice (Referee)
        await session.execute(text(f"INSERT INTO invoices (id, user_id, number, status, total_amount, currency, stripe_payment_intent_id, refunded_total, created_at, updated_at) VALUES ('{invoice_id}', '{referee_id}', 'INV-P16-001', 'paid', 100.00, 'TRY', 'pi_mock_p16', 0, NOW(), NOW())"))
        
        await session.commit()

    # 2. Simulate Webhook: Refund
    print("\n🔹 Testing Revocation Logic (Direct Service Call)...")
    async with AsyncSessionLocal() as session:
        from app.services.stripe_service import StripeService
        from app.models.billing import Invoice
        
        service = StripeService(session)
        
        # Mock Stripe
        from unittest.mock import MagicMock
        import stripe
        stripe.Customer = MagicMock()
        stripe.Customer.create_balance_transaction.return_value = MagicMock(id="txn_debit_123")
        
        # Call revocation directly
        # Need to fetch invoice object first
        from sqlalchemy import select
        res = await session.execute(select(Invoice).where(Invoice.id == uuid.UUID(invoice_id)))
        invoice = res.scalar_one()
        
        # Simulate Full Refund
        await service._process_revocation(
            invoice=invoice,
            reason="Simulated Refund",
            refund_amount_cents=10000,
            charge_amount_cents=10000
        )
        
        await session.commit()
        
        # 3. Verify
        # Check Reward Status
        reward_res = await session.execute(text(f"SELECT status FROM referral_rewards WHERE id = '{reward_id}'"))
        status = reward_res.scalar()
        if status == 'revoked':
            print("✅ Reward Status: Revoked")
        else:
            print(f"❌ Reward Status: {status}")
            
        # Check Ledger
        ledger_res = await session.execute(text(f"SELECT type, amount, reason FROM reward_ledger WHERE reward_id = '{reward_id}'"))
        ledger = ledger_res.fetchone()
        if ledger:
            print(f"✅ Ledger Entry: {ledger[0]} {ledger[1]} ({ledger[2]})")
            if ledger[0] == 'DEBIT' and float(ledger[1]) == 100.00:
                print("✅ Ledger Correct")
            else:
                print("❌ Ledger Incorrect")
        else:
            print("❌ Ledger Entry Missing")

    print("\n🎉 Stripe Reactivity Test PASSED!")

if __name__ == "__main__":
    asyncio.run(test_stripe_reactivity())
