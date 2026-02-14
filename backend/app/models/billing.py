
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

# StripeEvent was defined in app.models.payment with a different schema (UUID PK vs String PK in P11)
# P11 redefinition wants String PK (evt_...) to match Stripe ID directly.
# Option 1: Drop old table and recreate with new schema (since it's dev/beta).
# Option 2: Use extend_existing=True but that doesn't change column type if table exists.
# We will define it here with a DIFFERENT name to avoid conflict in metadata if both imported, 
# OR we rely on the migration script to handle the schema change.
# Let's use `BillingStripeEvent` or rely on `app.models.payment` if it's sufficient.
# `app.models.payment` has: id(UUID), event_id(String), event_type(String).
# This is actually fine. We can use `event_id` for idempotency check.
# So we DON'T need to redefine `StripeEvent` here if we import `app.models.payment`.
# BUT, P11 architecture spec asked for `stripe_events` table.
# Let's assume we use `app.models.payment.StripeEvent` for P11 too.

# Re-exporting for convenience if needed, but avoiding redefinition.
from app.models.payment import StripeEvent

# Similarly for Invoice
from app.models.billing import Invoice, InvoiceItem, VatRate
