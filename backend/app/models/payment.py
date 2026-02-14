
"""
P2: Stripe & Payment Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class StripeSettings(Base):
    """Country-based Stripe Configuration"""
    __tablename__ = "stripe_settings"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    country: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    
    # Feature toggle
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Credentials
    secret_key_env_key: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "STRIPE_SECRET_DE"
    webhook_secret_env_key: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "STRIPE_WEBHOOK_SECRET_DE"
    publishable_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Safe to store
    
    # Account mode
    account_mode: Mapped[str] = mapped_column(String(20), default="test") # test / live
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PaymentAttempt(Base):
    """Log of payment attempts for an invoice"""
    __tablename__ = "payment_attempts"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    # Snapshot of attempt details
    country: Mapped[str] = mapped_column(String(5), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    amount_gross: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Stripe Metadata
    stripe_checkout_session_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Status: created, processing, succeeded, failed, canceled
    status: Mapped[str] = mapped_column(String(20), default="created", index=True)
    
    # Errors
    failure_code: Mapped[Optional[str]] = mapped_column(String(50))
    failure_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# P11: StripeEvent defined in app.models.billing now
# Removed here to avoid conflict

class Refund(Base):
    """Refund records"""
    __tablename__ = "refunds"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    payment_attempt_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("payment_attempts.id"), nullable=True)
    
    stripe_refund_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="requested") # requested, succeeded, failed
    failure_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    created_by_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
