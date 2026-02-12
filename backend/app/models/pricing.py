
"""
P5: Pricing Engine Models (Versioned & Enforced)
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Numeric, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone, date
from typing import Optional
from decimal import Decimal
import uuid
from app.models.base import Base

class CountryCurrencyMap(Base):
    """Country to Currency Enforcement"""
    __tablename__ = "country_currency_map"
    
    country: Mapped[str] = mapped_column(String(5), primary_key=True)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class PriceConfig(Base):
    """Fiyat Matrisi (Versioned)"""
    __tablename__ = "price_configs"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    country: Mapped[str] = mapped_column(String(5), ForeignKey("country_currency_map.country"), nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # individual, dealer
    pricing_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # pay_per_listing, highlight_fee, etc.
    
    unit_price_net: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False) # Must match map via app logic or trigger/constraint, enforced here via check?
    
    price_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_price_configs_active_unique', 'country', 'segment', 'pricing_type', unique=True, postgresql_where=(is_active == True)),
        CheckConstraint('unit_price_net >= 0', name='check_price_positive'),
    )

class FreeQuotaConfig(Base):
    """Ücretsiz Kota Tanımları (Versioned)"""
    __tablename__ = "free_quota_configs"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    segment: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    quota_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False) # Rolling window days
    period_type: Mapped[str] = mapped_column(String(20), default="rolling") # rolling, fixed
    quota_scope: Mapped[str] = mapped_column(String(50), default="listing_only")
    
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_free_quota_configs_active_unique', 'country', 'segment', unique=True, postgresql_where=(is_active == True)),
        CheckConstraint('quota_amount >= 0', name='check_quota_positive'),
    )

class Discount(Base):
    """İndirim Kuralları"""
    __tablename__ = "discounts"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False) # percentage, fixed_amount
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    country_scope: Mapped[str] = mapped_column(String(5), nullable=False) # "ALL" or "DE"
    segment_scope: Mapped[str] = mapped_column(String(20), nullable=False) # "ALL" or "dealer"
    apply_to: Mapped[str] = mapped_column(String(50), nullable=False) # package, per_listing, all
    
    stacking_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        CheckConstraint('value >= 0', name='check_discount_value_positive'),
    )

class ListingConsumptionLog(Base):
    """Kullanım Takibi (Immutable Ledger)"""
    __tablename__ = "listing_consumption_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    listing_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listings.id"), nullable=False, index=True)
    dealer_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("dealers.id"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    consumed_source: Mapped[str] = mapped_column(String(50), nullable=False) # free_quota, subscription_quota, paid_extra
    
    # Snapshot references
    price_config_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("price_configs.id"), nullable=True)
    invoice_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoice_items.id"), nullable=True)
    
    charged_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_consumption_logs_composite', 'dealer_id', 'consumed_source', 'created_at'),
        # Immutable check constraint is hard in PG without triggers, enforced in app logic + API design (no update endpoint)
    )
