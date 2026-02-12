"""
P1-1: Dealer Management Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import enum
from app.models.base import Base

class DealerType(str, enum.Enum):
    AUTO_DEALER = "auto_dealer"
    REAL_ESTATE_AGENCY = "real_estate_agency"
    MACHINERY_DEALER = "machinery_dealer"
    GENERAL = "general"

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class DealerApplication(Base):
    """Dealer başvuru modeli"""
    __tablename__ = "dealer_applications"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Country scope
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    # Dealer type
    dealer_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Company info
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_tax_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Contact info
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_dealer_applications_country_status', 'country', 'status'),
    )

class Dealer(Base):
    """Onaylanmış Dealer entity"""
    __tablename__ = "dealers"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("dealer_applications.id"), nullable=False, unique=True)
    
    # Country scope
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    dealer_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    # Company info (copied from application)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_tax_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status & Permissions
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    can_publish: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Limits
    listing_limit: Mapped[int] = mapped_column(Integer, default=50)
    premium_limit: Mapped[int] = mapped_column(Integer, default=10)
    
    # Stats (cached)
    active_listing_count: Mapped[int] = mapped_column(Integer, default=0)
    total_listing_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    users: Mapped[List["DealerUser"]] = relationship("DealerUser", back_populates="dealer", lazy="selectin")
    
    __table_args__ = (
        Index('ix_dealers_country_active', 'country', 'is_active'),
    )

class DealerUser(Base):
    """Dealer-User many-to-many with role"""
    __tablename__ = "dealer_users"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("dealers.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Role in dealer: owner, staff
    role_in_dealer: Mapped[str] = mapped_column(String(20), default="staff", nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    dealer: Mapped["Dealer"] = relationship("Dealer", back_populates="users")
    
    __table_args__ = (
        Index('ix_dealer_users_unique', 'dealer_id', 'user_id', unique=True),
    )
