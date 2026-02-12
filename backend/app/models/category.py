"""
P0-1: Category System with N-level hierarchy using Materialized Path
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional, List
import uuid
from app.models.base import Base

class Category(Base):
    __tablename__ = "categories"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Materialized Path - e.g., "1.5.12" for fast tree queries
    path: Mapped[str] = mapped_column(String(500), nullable=False, default="", index=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Module association (real_estate, vehicle, machinery, services, jobs)
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Slug per language for URLs
    slug: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "emlak", "de": "immobilien", "fr": "immobilier"}
    
    # Icon and image
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_visible_on_home: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # Soft delete
    
    # Inheritance / Override flags
    inherit_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    override_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    inherit_countries: Mapped[bool] = mapped_column(Boolean, default=True)
    override_countries: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Allowed countries (if not inherited)
    allowed_countries: Mapped[list] = mapped_column(JSON, default=list)  # ["DE", "CH", "FR", "AT"]
    
    # Listing stats (cached)
    listing_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    translations: Mapped[List["CategoryTranslation"]] = relationship("CategoryTranslation", back_populates="category", lazy="selectin")
    
    __table_args__ = (
        Index('ix_categories_module_enabled', 'module', 'is_enabled', 'is_deleted'),
        Index('ix_categories_path_prefix', 'path', postgresql_ops={'path': 'text_pattern_ops'}),
    )

class CategoryTranslation(Base):
    __tablename__ = "category_translations"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    category: Mapped["Category"] = relationship("Category", back_populates="translations")
    
    __table_args__ = (
        Index('ix_category_translations_unique', 'category_id', 'language', unique=True),
    )
