"""
P1-2: Premium Product Catalog & Listing Promotion Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal
import uuid
from app.models.base import Base

class PremiumProduct(Base):
    """Premium ürün kataloğu (Vitrin, Öne Çıkar, Üste Taşı, Süre Uzat)"""
    __tablename__ = "premium_products"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Product key: SHOWCASE, FEATURED, BUMP, EXTEND
    key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Translations
    name: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "Vitrin", "de": "Schaufenster", "fr": "Vitrine"}
    description: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Country & Currency
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)  # EUR, CHF
    
    # Pricing (net, before tax)
    price_net: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Duration
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Tax category for VAT calculation
    tax_category: Mapped[str] = mapped_column(String(50), default="digital_service")  # digital_service, advertising
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_premium_products_country_key', 'country', 'key', unique=True),
        Index('ix_premium_products_active', 'is_active', 'country'),
    )

class ListingPromotion(Base):
    """İlan promotion kaydı"""
    __tablename__ = "listing_promotions"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # References
    listing_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("premium_products.id"), nullable=False, index=True)
    
    # Time window
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Ranking
    priority_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Admin who applied
    created_by_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_listing_promotions_listing_active', 'listing_id', 'is_active'),
        Index('ix_listing_promotions_dates', 'start_at', 'end_at'),
    )

class PremiumRankingRule(Base):
    """Country bazlı premium sıralama kuralları"""
    __tablename__ = "premium_ranking_rules"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    country: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    
    # Premium öncelik
    premium_first: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Ağırlıklar (0-100)
    weight_priority: Mapped[int] = mapped_column(Integer, default=50)
    weight_recency: Mapped[int] = mapped_column(Integer, default=50)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
