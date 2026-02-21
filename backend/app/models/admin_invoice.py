from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Index, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base


class AdminInvoice(Base):
    __tablename__ = "admin_invoices"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_no: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("user_subscriptions.id"), nullable=True)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=True, index=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    amount_total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(5), nullable=False, server_default="EUR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="draft")
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="requires_payment_method")
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_customer_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, server_default="country")
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_admin_invoices_user", "user_id"),
        Index("ix_admin_invoices_status", "status"),
        Index("ix_admin_invoices_created", "created_at"),
    )
