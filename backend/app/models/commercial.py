
"""
P4: Dealer Packages & Subscriptions
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal
import uuid
from app.models.base import Base

class DealerPackage(Base):
    """Satılabilir Bayi Paketleri (Fixed Duration)"""
    __tablename__ = "dealer_packages"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Key: BASIC, PRO, ENTERPRISE
    key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Scope
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    # Display
    name: Mapped[dict] = mapped_column(JSON, nullable=False) # i18n
    description: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Pricing
    price_net: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False) # EUR, CHF
    
    # Duration
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False) # e.g. 30, 365
    
    # Limits & Quotas provided by this package
    listing_limit: Mapped[int] = mapped_column(Integer, default=0)
    premium_quota: Mapped[int] = mapped_column(Integer, default=0)
    highlight_quota: Mapped[int] = mapped_column(Integer, default=0)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_dealer_packages_country_active', 'country', 'is_active'),
    )

class DealerSubscription(Base):
    """Bayi Abonelik Kaydı"""
    __tablename__ = "dealer_subscriptions"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    dealer_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("dealers.id"), nullable=False, index=True)
    package_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("dealer_packages.id"), nullable=False)
    
    # Linked Invoice (Proof of payment)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, unique=True)
    
    # Period
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True) # pending, active, expired, cancelled
    
    # Consumption (Remaining Quotas)
    remaining_listing_quota: Mapped[int] = mapped_column(Integer, default=0)
    remaining_premium_quota: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    
    __table_args__ = (
        Index('ix_dealer_subscriptions_dealer_id', 'dealer_id'),
        Index('ix_dealer_subscriptions_end_at', 'end_at'),
        Index('ix_dealer_subscriptions_status', 'status'),
        # P5: Unique Active Subscription Constraint
        Index('ix_dealer_active_subscription', 'dealer_id', unique=True, postgresql_where=(status == 'active')),
    )
        # P5: Unique Invoice Constraint (One active sub per payment)
        Index('ix_dealer_subscriptions_invoice', 'invoice_id', unique=True),