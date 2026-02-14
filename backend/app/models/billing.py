
"""
P11 Billing Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base

class BillingCustomer(Base):
    __tablename__ = "billing_customers"
    
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    stripe_customer_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    balance: Mapped[Numeric] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default='TRY')
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class StripeSubscription(Base):
    __tablename__ = "stripe_subscriptions"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True) # sub_...
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    plan_code: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. DEALER_TR_PRO
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # active, past_due, canceled
    
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class StripeEvent(Base):
    __tablename__ = "stripe_events"
    
    id: Mapped[str] = mapped_column(String(100), primary_key=True) # evt_...
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processed")
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
