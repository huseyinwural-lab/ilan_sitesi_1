
"""
P11 Billing Models (Revised to avoid circular imports)
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base

# --- P11 New Tables ---

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

# --- P1 Legacy/Compat Definitions (Redefined here to break circular dependency) ---
# In a real refactor, we would move these to app.models.invoice or similar.
# For now, we define them here if not already defined in metadata by another import.
# Using extend_existing=True allows re-definition if already imported via app.models.payment -> ...

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    
    total_amount: Mapped[Numeric] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(5), default="TRY")
    
    pdf_url: Mapped[str] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    
class VatRate(Base):
    __tablename__ = "vat_rates"
    __table_args__ = {'extend_existing': True}
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country: Mapped[str] = mapped_column(String(5))
    rate: Mapped[Numeric] = mapped_column(Numeric(5, 2))
    tax_type: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
