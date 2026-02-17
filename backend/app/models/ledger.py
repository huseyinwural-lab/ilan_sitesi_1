
"""
P16: Reward Ledger Models
"""
from sqlalchemy import String, Integer, ForeignKey, Index, Numeric, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base

class RewardLedger(Base):
    __tablename__ = "reward_ledger"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    reward_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("referral_rewards.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction Type: CREDIT (Add to balance), DEBIT (Remove from balance)
    type: Mapped[str] = mapped_column(String(20), nullable=False) 
    
    amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY")
    
    reason: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "maturity", "revocation", "manual_adjustment"
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
