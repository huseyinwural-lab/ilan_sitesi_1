
"""
P10 Monetization Engine Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base
from app.models.plan import Plan

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # DEALER_TR_PRO
    
    name: Mapped[dict] = mapped_column(JSON, nullable=False) # {"en": "Pro Plan"}
    description: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    price: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False) # TRY, EUR
    discount_percent: Mapped[Numeric] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False) # 30
    limits: Mapped[dict] = mapped_column(JSON, nullable=False) # {"listing": 50, "showcase": 5}
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, server_default='TR')

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="trial", index=True)

    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="stripe")
    provider_customer_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    plan: Mapped["Plan"] = relationship("Plan")

    __table_args__ = (
        Index('ix_user_subscriptions_user', 'user_id', unique=True),
        Index('ix_user_subscriptions_status', 'status'),
    )

class QuotaUsage(Base):
    __tablename__ = "quota_usage"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False) # listing_active
    
    used: Mapped[int] = mapped_column(Integer, default=0)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_quota_usage_user_resource', 'user_id', 'resource', unique=True),
    )
