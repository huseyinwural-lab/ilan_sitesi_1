
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.ledger import RewardLedger
from app.models.user import User
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)

class LedgerService:
    MIN_WITHDRAW_AMOUNT = Decimal("50.00")

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_net_balance(self, user_id: str) -> Decimal:
        """
        Calculates net balance from immutable ledger.
        Formula: Credits - Debits - Payouts (if payouts stored in ledger as DEBIT or separate type)
        Assumption: Payouts are recorded as 'PAYOUT' type (which acts like DEBIT).
        """
        stmt = select(
            RewardLedger.type,
            func.sum(RewardLedger.amount)
        ).where(RewardLedger.user_id == uuid.UUID(user_id)).group_by(RewardLedger.type)
        
        result = await self.db.execute(stmt)
        sums = {row[0]: row[1] for row in result.all()}
        
        total_credit = sums.get("CREDIT", Decimal(0))
        total_debit = sums.get("DEBIT", Decimal(0))
        total_payout = sums.get("PAYOUT", Decimal(0)) # Future proofing
        
        net = total_credit - total_debit - total_payout
        return net

    async def can_withdraw(self, user_id: str, amount: Decimal) -> bool:
        # 1. Check User Status
        user_res = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active:
            return False
            
        # 2. Minimum Threshold
        if amount < self.MIN_WITHDRAW_AMOUNT:
            return False

        # 3. Balance Check
        balance = await self.get_net_balance(user_id)
        
        # Must have enough balance AND not be in negative state
        if balance < 0:
            return False
            
        if balance < amount:
            return False
            
        return True
