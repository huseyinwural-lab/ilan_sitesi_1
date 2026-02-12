"""
P0-2: Attribute Engine for dynamic form fields
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional, List
import uuid
from app.models.base import Base

class Attribute(Base):
    __tablename__ = "attributes"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Translations for name and placeholder
    name: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "Oda Sayısı", "de": "Zimmeranzahl", "fr": "Nombre de pièces"}
    placeholder: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    help_text: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Type: text, number, select, multi_select, boolean, date, range, textarea
    attribute_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Validation
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    min_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    regex_pattern: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Search/Filter/Sort capabilities
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_sortable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Display
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # m², km, €
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    options: Mapped[List["AttributeOption"]] = relationship("AttributeOption", back_populates="attribute", lazy="selectin")
    category_mappings: Mapped[List["CategoryAttributeMap"]] = relationship("CategoryAttributeMap", back_populates="attribute", lazy="selectin")

class AttributeOption(Base):
    __tablename__ = "attribute_options"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribute_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "2+1", "de": "2+1", "fr": "2+1"}
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationship
    attribute: Mapped["Attribute"] = relationship("Attribute", back_populates="options")
    
    __table_args__ = (
        Index('ix_attribute_options_attr_value', 'attribute_id', 'value', unique=True),
    )

class CategoryAttributeMap(Base):
    __tablename__ = "category_attribute_map"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Override settings for this category
    is_required_override: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    display_order_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Inheritance
    inherit_to_children: Mapped[bool] = mapped_column(Boolean, default=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    attribute: Mapped["Attribute"] = relationship("Attribute", back_populates="category_mappings")
    
    __table_args__ = (
        Index('ix_category_attribute_map_unique', 'category_id', 'attribute_id', unique=True),
    )
