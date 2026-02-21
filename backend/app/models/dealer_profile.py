from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import Optional
import uuid
from app.models.base import Base

class DealerProfile(Base):
    __tablename__ = "dealer_profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True, index=True)

    # Identity
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_number: Mapped[str] = mapped_column(String(50), nullable=True) # Optional initially
    
    # Address
    address_street: Mapped[str] = mapped_column(String(255), nullable=True)
    address_zip: Mapped[str] = mapped_column(String(20), nullable=True)
    address_city: Mapped[str] = mapped_column(String(100), nullable=True)
    address_country: Mapped[str] = mapped_column(String(5), default="DE")
    
    # Contact (Publicly visible)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Legal Texts (Rich Text / Markdown)
    impressum_text: Mapped[str] = mapped_column(Text, nullable=True)
    terms_text: Mapped[str] = mapped_column(Text, nullable=True)
    withdrawal_policy_text: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status
    verification_status: Mapped[str] = mapped_column(String(20), default="pending") # pending, verified, rejected
