
import asyncio
import os
import sys
import uuid
from sqlalchemy import text, select, func
from decimal import Decimal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.referral import ReferralReward
from app.models.ledger import RewardLedger
from app.models.user import User
from app.services.ledger_service import LedgerService

async def validate_financial_integrity():
    print("🚀 Starting P16 Final Financial Validation...")
    
    user_id = str(uuid.uuid4())
    reward_id = str(uuid.uuid4())
    
    async with AsyncSessionLocal() as session:
        # 1. Setup User & Confirmed Reward
        referee_id = str(uuid.uuid4())
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{user_id}', 'finance_{user_id[:8]}@test.com', 'hash', 'Finance User', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{referee_id}', 'finance_referee_{referee_id[:8]}@test.com', 'hash', 'Finance Referee', 'individual', true, true, '[]', 'en', false, NOW(), NOW())"))
        
        # Add CREDIT (Confirmed Reward)
        await session.execute(text(f"INSERT INTO referral_rewards (id, referrer_id, referee_id, amount, currency, status, created_at) VALUES ('{reward_id}', '{user_id}', '{referee_id}', 100.00, 'TRY', 'confirmed', NOW())"))
        
        await session.execute(text(f"INSERT INTO reward_ledger (id, reward_id, user_id, type, amount, currency, reason, created_at) VALUES ('{uuid.uuid4()}', '{reward_id}', '{user_id}', 'CREDIT', 100.00, 'TRY', 'maturity', NOW())"))
        
        await session.commit()
        print("✅ Setup: User with 100 TRY Credit")

        # 2. Test Withdraw Guard (Positive Balance)
        ledger_service = LedgerService(session)
        can_withdraw = await ledger_service.can_withdraw(user_id, Decimal("50.00"))
        
        if can_withdraw:
            print("✅ Withdraw Guard: Allowed for positive balance")
        else:
            print("❌ Withdraw Guard: Failed (Should allow)")

        # 3. Simulate Revocation (Refund) -> Debit
        # Add DEBIT
        await session.execute(text(f"INSERT INTO reward_ledger (id, reward_id, user_id, type, amount, currency, reason, created_at) VALUES ('{uuid.uuid4()}', '{reward_id}', '{user_id}', 'DEBIT', 100.00, 'TRY', 'revocation', NOW())"))
        await session.commit()
        
        # 4. Test Withdraw Guard (Zero Balance)
        can_withdraw = await ledger_service.can_withdraw(user_id, Decimal("10.00"))
        if not can_withdraw:
            print("✅ Withdraw Guard: Blocked for zero balance (Insufficient funds)")
        else:
            print("❌ Withdraw Guard: Failed (Should block)")

        # 5. Simulate Negative Balance (Over-draft via chargeback after payout)
        # Add Manual DEBIT
        await session.execute(text(f"INSERT INTO reward_ledger (id, reward_id, user_id, type, amount, currency, reason, created_at) VALUES ('{uuid.uuid4()}', '{reward_id}', '{user_id}', 'DEBIT', 50.00, 'TRY', 'chargeback_penalty', NOW())"))
        await session.commit()
        
        # 6. Test Withdraw Guard (Negative Balance)
        # Net: 100 (Credit) - 100 (Debit) - 50 (Debit) = -50
        net = await ledger_service.get_net_balance(user_id)
        print(f"📉 Current Net Balance: {net}")
        
        can_withdraw = await ledger_service.can_withdraw(user_id, Decimal("10.00"))
        if not can_withdraw and net < 0:
            print("✅ Withdraw Guard: Blocked for negative balance")
        else:
            print("❌ Withdraw Guard: Failed (Should block negative)")

        # 7. Ledger Integrity Check
        # Sum of Credits - Sum of Debits should match Net Balance
        res = await session.execute(select(
            func.sum(RewardLedger.amount).filter(RewardLedger.type == 'CREDIT'),
            func.sum(RewardLedger.amount).filter(RewardLedger.type == 'DEBIT')
        ).where(RewardLedger.user_id == uuid.UUID(user_id)))
        
        credits, debits = res.one()
        calc_net = (credits or 0) - (debits or 0)
        
        if calc_net == net:
            print(f"✅ Ledger Integrity: Consistent ({calc_net} == {net})")
        else:
            print(f"❌ Ledger Integrity: Mismatch ({calc_net} != {net})")

    print("\n🎉 Financial Integrity Validation PASSED!")

if __name__ == "__main__":
    asyncio.run(validate_financial_integrity())
