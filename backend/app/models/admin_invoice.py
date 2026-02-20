from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base


class AdminInvoice(Base):
    __tablename__ = "admin_invoices"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    dealer_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(5), nullable=False, server_default="EUR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, server_default="country")
    country_code: Mapped[str] = mapped_column(String(10), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_admin_invoices_status", "status"),
        Index("ix_admin_invoices_country", "country_code"),
    )
