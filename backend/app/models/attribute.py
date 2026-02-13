"""
P0-2: Attribute System (Category-Specific Attributes)
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional, List
import uuid
from app.models.base import Base

class Attribute(Base):
    """Dynamic Attribute Definition (e.g. Size, Color, KM)"""
    __tablename__ = "attributes"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[dict] = mapped_column(JSON, nullable=False) # {"en": "Size", "tr": "Beden"}
    
    # Type: text, number, select, multi_select, boolean, date
    attribute_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Validation
    is_required: Mapped[bool] = mapped_column(Boolean, default=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # kg, m2, km
    
    # Features
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sortable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # P6 Shopping: Variant Logic
    is_variant: Mapped[bool] = mapped_column(Boolean, server_default='false', nullable=False)
    
    # UI
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    options: Mapped[List["AttributeOption"]] = relationship("AttributeOption", back_populates="attribute", cascade="all, delete-orphan")

class AttributeOption(Base):
    """Options for Select/Multi-Select Attributes"""
    __tablename__ = "attribute_options"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    attribute_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("attributes.id"), nullable=False, index=True)
    
    value: Mapped[str] = mapped_column(String(100), nullable=False) # Internal value (slug)
    label: Mapped[dict] = mapped_column(JSON, nullable=False) # Display label {"en": "Red"}
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    attribute: Mapped["Attribute"] = relationship("Attribute", back_populates="options")

class CategoryAttributeMap(Base):
    """Link Categories to Attributes"""
    __tablename__ = "category_attribute_map"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    category_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("attributes.id"), nullable=False, index=True)
    
    is_required_override: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    inherit_to_children: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ListingAttribute(Base):
    """Typed Attribute Values for Listings (EAV) - P6 S2"""
    __tablename__ = "listing_attributes"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    listing_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("attributes.id"), nullable=False, index=True)
    
    # Typed Values
    value_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    value_number: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    value_boolean: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_option_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("attribute_options.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_listing_attributes_attr_val_opt', 'attribute_id', 'value_option_id'),
        Index('ix_listing_attributes_attr_val_num', 'attribute_id', 'value_number'),
    )
