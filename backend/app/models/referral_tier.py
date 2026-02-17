
"""
P18: Referral Tier Models
"""
from sqlalchemy import String, Integer, ForeignKey, Index, Numeric, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class ReferralTier(Base):
    __tablename__ = "referral_tiers"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False) # Standard, Gold, Platinum
    min_count: Mapped[int] = mapped_column(Integer, nullable=False, unique=True) # 0, 5, 20
    
    reward_amount: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TRY")
    
    badge_icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Note: User model extension (referral_tier_id, referral_count_confirmed) 
# will be handled in migration script or separate mixin if possible, 
# but usually we modify User model directly or use Alembic to add columns.
# We will modify User model definition in app/models/user.py as well.
