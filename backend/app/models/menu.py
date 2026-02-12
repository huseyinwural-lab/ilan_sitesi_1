"""
P0-3: Top Menu / Mega Menu Management
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional, List
import uuid
from app.models.base import Base

class TopMenuItem(Base):
    """Top level menu items (Emlak, Vasıta, Yedek Parça, etc.)"""
    __tablename__ = "top_menu_items"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Translations
    name: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"}
    
    # Display
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    badge: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"text": "Yeni", "color": "orange"}
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Feature flag dependency
    required_module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Links to feature_flags.key
    
    # Country scope
    allowed_countries: Mapped[list] = mapped_column(JSON, default=list)  # ["DE", "CH"] or ["*"]
    
    # Status
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    sections: Mapped[List["TopMenuSection"]] = relationship("TopMenuSection", back_populates="menu_item", lazy="selectin")
    
    __table_args__ = (
        Index('ix_top_menu_items_enabled_sort', 'is_enabled', 'sort_order'),
    )

class TopMenuSection(Base):
    """Sections within a mega menu (Popular, By Type, By Location, etc.)"""
    __tablename__ = "top_menu_sections"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    menu_item_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("top_menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Translations
    title: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "Popüler", "de": "Beliebt", "fr": "Populaire"}
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Country scope
    allowed_countries: Mapped[list] = mapped_column(JSON, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    menu_item: Mapped["TopMenuItem"] = relationship("TopMenuItem", back_populates="sections")
    links: Mapped[List["TopMenuLink"]] = relationship("TopMenuLink", back_populates="section", lazy="selectin")

class TopMenuLink(Base):
    """Individual links within a menu section"""
    __tablename__ = "top_menu_links"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("top_menu_sections.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Translations
    label: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "Satılık Daireler", "de": "Wohnungen zum Verkauf", "fr": "Appartements à vendre"}
    
    # Link type: category, pre_filtered, static_page, external
    link_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Target reference based on link_type
    # category: category_id
    # pre_filtered: query params JSON
    # static_page: page slug
    # external: full URL
    target_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Optional: open in new tab
    open_new_tab: Mapped[bool] = mapped_column(Boolean, default=False)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Country scope
    allowed_countries: Mapped[list] = mapped_column(JSON, default=list)
    
    # Show "View All" style
    is_view_all: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    section: Mapped["TopMenuSection"] = relationship("TopMenuSection", back_populates="links")
