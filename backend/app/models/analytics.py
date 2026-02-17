from sqlalchemy import String, DateTime, ForeignKey, Index, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class ListingView(Base):
    __tablename__ = "listing_views"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_listing_views_dedup', 'listing_id', 'ip_hash', 'created_at'),
    )

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Core
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # For anonymous tracking
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Dimensions (First-class columns for Indexing)
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listings.id"), nullable=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Rich Context
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_interactions_user_event', 'user_id', 'event_type', 'created_at'),
        Index('ix_interactions_listing_event', 'listing_id', 'event_type'),
        Index('ix_interactions_type_date', 'event_type', 'created_at'),
    )

class UserFeature(Base):
    __tablename__ = "user_features"
    
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    
    # Feature Vectors
    category_affinity: Mapped[dict] = mapped_column(JSONB, default={})
    city_affinity: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Derived Scalar Features
    price_sensitivity: Mapped[float] = mapped_column(Float, default=0.0) # 0.0 - 1.0 (Percentile)
    activity_score: Mapped[float] = mapped_column(Float, default=0.0) # 0.0 - 10.0
    
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
