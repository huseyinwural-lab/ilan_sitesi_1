"""
P1-4: Tax/VAT + Invoice Core Models
"""
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, Index, Numeric, Sequence
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone, date
from typing import Optional, List
from decimal import Decimal
import uuid
from app.models.base import Base

class VatRate(Base):
    """VAT oranları (ülke bazlı, tarih aralıklı)"""
    __tablename__ = "vat_rates"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    
    # Rate as percentage (e.g., 19.0 for 19%)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    
    # Validity period
    valid_from: Mapped[date] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Tax type (standard, reduced, zero)
    tax_type: Mapped[str] = mapped_column(String(20), default="standard")
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_vat_rates_country_dates', 'country', 'valid_from', 'valid_to'),
    )

# Invoice number sequence
invoice_number_seq = Sequence('invoice_number_seq', start=1000)

class Invoice(Base):
    """Fatura çekirdeği"""
    __tablename__ = "invoices"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Invoice number: country prefix + sequence (e.g., DE-2026-001000)
    invoice_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Country & Currency
    country: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    
    # Customer
    customer_type: Mapped[str] = mapped_column(String(20), nullable=False)  # individual, dealer
    customer_ref_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_vat_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Status: draft, paid, cancelled
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    
    # Totals
    net_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    gross_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    
    # Tax snapshot at invoice time
    tax_rate_snapshot: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    
    # Dates
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Stripe & Payment (P2)
    payment_idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    billing_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True) # Full snapshot of customer billing info at time of invoice

    refunded_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    refund_status: Mapped[str] = mapped_column(String(20), default="none") # none, partial, full
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    items: Mapped[List["InvoiceItem"]] = relationship("InvoiceItem", back_populates="invoice", lazy="selectin")
    
    __table_args__ = (
        Index('ix_invoices_country_status', 'country', 'status'),
        Index('ix_invoices_customer', 'customer_type', 'customer_ref_id'),
    )

class InvoiceItem(Base):
    """Fatura kalemleri"""
    __tablename__ = "invoice_items"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Item type: premium_product, ad_slot, other
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Reference to original item (e.g., premium_product_id)
    ref_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    
    # Description
    description: Mapped[dict] = mapped_column(JSON, nullable=False)  # {"tr": "...", "de": "...", "fr": "..."}
    
    # Quantity & Pricing
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_net: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    # Line totals
    line_net: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_gross: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="items")
