
"""
P14: Promotion Engine Models
"""
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Index, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class Promotion(Base):
    __tablename__ = "promotions"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    promo_type: Mapped[str] = mapped_column(String(20), nullable=False) # percentage, fixed_amount
    value: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_redemptions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Global limit for this promotion campaign
    
    stripe_coupon_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Coupon(Base):
    __tablename__ = "coupons"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    promotion_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("promotions.id"), nullable=False, index=True)
    
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Limit for this specific code
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    promotion: Mapped["Promotion"] = relationship("Promotion")

class CouponRedemption(Base):
    __tablename__ = "coupon_redemptions"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    coupon_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("coupons.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True, index=True)
    
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    discount_amount: Mapped[Optional[Numeric]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Enforce one usage per coupon per user (as per decision)
    # Note: If per_user_limit > 1 is needed later, we remove this unique constraint or add a counter.
    # Architecture Decision 3 says: "User Başına 1 Kullanım"
    __table_args__ = (
        Index('ix_coupon_redemptions_user_coupon', 'user_id', 'coupon_id', unique=True),
    )
