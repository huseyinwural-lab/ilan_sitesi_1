"""
P1-3: Moderation Queue Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Enum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import Float
from datetime import datetime, timezone
from typing import Optional, List
import uuid
from app.models.base import Base

PRICE_TYPE_ENUM = Enum("FIXED", "HOURLY", name="price_type_enum")

class Listing(Base):
    """Listing modeli (minimum - moderation için)"""
    __tablename__ = "listings"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Module & Category
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Location
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_accuracy: Mapped[str] = mapped_column(String(20), default="approximate")
    # Pricing
    price_type: Mapped[str] = mapped_column(PRICE_TYPE_ENUM, nullable=False, server_default="FIXED")
    price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(5), default="EUR")
    
    # Owner
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    dealer_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    is_dealer_listing: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Images
    images: Mapped[list] = mapped_column(JSON, default=list)  # ["url1", "url2"]
    image_count: Mapped[int] = mapped_column(Integer, default=0)
    
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    # Attributes
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)  # {"room_count": 3, "area": 120}
    
    # Vehicle Master Data (Added in P6 S2)
    make_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("vehicle_makes.id"), nullable=True)
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("vehicle_models.id"), nullable=True)
    
    # Contact options
    contact_option_phone: Mapped[bool] = mapped_column(Boolean, default=True)
    contact_option_message: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status: pending, active, rejected, suspended, expired
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    user_type_snapshot: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    moderated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    rejected_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Premium
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    
    # Showcase / Doping (P13 + P88)
    is_showcase: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    showcase_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    featured_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    urgent_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Showcase (Added in P13)
    is_showcase: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    showcase_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        CheckConstraint("NOT (price IS NOT NULL AND hourly_rate IS NOT NULL)", name="ck_listings_price_single_mode"),
        Index('ix_listings_country_status', 'country', 'status'),
        Index('ix_listings_module_status', 'module', 'status'),
        Index('ix_listings_moderation', 'status', 'country', 'module', 'created_at'),
        Index('ix_listings_featured_until', 'featured_until'),
        Index('ix_listings_urgent_until', 'urgent_until'),
        Index('ix_listings_paid_until', 'paid_until'),
        Index('ix_listings_make_id', 'make_id'),
        Index('ix_listings_model_id', 'model_id'),
    )

class ModerationItem(Base):
    """Moderation Item (SQL)"""
    __tablename__ = "moderation_items"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderator_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    audit_ref: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_moderation_items_status_created', 'status', 'created_at'),
        Index('ix_moderation_items_listing', 'listing_id'),
    )


class ModerationQueue(Base):
    """Legacy moderation_queue karşılığı (SQL)"""
    __tablename__ = "moderation_queue"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderator_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_moderation_queue_status_created', 'status', 'created_at'),
        Index('ix_moderation_queue_listing', 'listing_id'),
    )


class ModerationAction(Base):
    """Moderasyon aksiyonları kaydı"""
    __tablename__ = "moderation_actions"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    listing_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Action: approve, reject, suspend, unsuspend
    action_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Reason (zorunlu for reject)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Actor
    actor_admin_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    actor_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_moderation_actions_listing_date', 'listing_id', 'created_at'),
    )

class ModerationRule(Base):
    """Country bazlı moderasyon kuralları"""
    __tablename__ = "moderation_rules"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    country: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    
    # Bad words filter
    bad_words_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    bad_words_list: Mapped[list] = mapped_column(JSON, default=list)  # ["word1", "word2"]
    bad_words_mode: Mapped[str] = mapped_column(String(20), default="warning")  # warning, block
    
    # Minimum images
    min_images_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_images_count: Mapped[int] = mapped_column(Integer, default=1)
    
    # Price sanity
    price_sanity_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    price_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Auto-approve for dealers
    auto_approve_dealers: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
