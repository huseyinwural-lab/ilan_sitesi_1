"""
P0-4: Home Layout Manager (Sol menü + Sağ 3 blok)
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class HomeLayoutSettings(Base):
    """Per-country home page layout settings"""
    __tablename__ = "home_layout_settings"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    
    # Block order: ["showcase", "special", "ads"] or reordered
    block_order: Mapped[list] = mapped_column(JSON, default=["showcase", "special", "ads"])
    
    # Mobile navigation mode: drawer, compact, tabbed
    mobile_nav_mode: Mapped[str] = mapped_column(String(20), default="drawer")
    
    # Show mega menu on desktop
    show_mega_menu: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Additional settings
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class HomeShowcaseItem(Base):
    """Vitrin - Featured listings on home page"""
    __tablename__ = "home_showcase_items"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to listing (will be a UUID when Listing model exists)
    listing_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Country scope
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Time-based visibility
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Who added this
    added_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_home_showcase_country_active', 'country_code', 'is_active', 'sort_order'),
    )

class HomeSpecialListing(Base):
    """Özel İlan - Special/promoted listings"""
    __tablename__ = "home_special_listings"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    listing_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Label translations
    label: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "Yeni", "de": "Neu", "fr": "Nouveau"}
    
    # Country scope
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    # Restrictions
    dealer_only: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_only: Mapped[bool] = mapped_column(Boolean, default=False)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    added_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_home_special_country_active', 'country_code', 'is_active', 'sort_order'),
    )

class AdSlot(Base):
    """Reklam - Advertisement slots"""
    __tablename__ = "ad_slots"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Placement: home_sidebar, home_banner, listing_detail, search_results
    placement: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Provider type: direct, adsense, header_bidding
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Country scope
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    # Content based on provider_type
    # direct: image_url, click_url
    # adsense: ad_client, ad_slot
    # header_bidding: config JSON
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    # For direct ads
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    click_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    alt_text: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Dimensions
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Tracking
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_ad_slots_placement_country', 'placement', 'country_code', 'is_active'),
    )
