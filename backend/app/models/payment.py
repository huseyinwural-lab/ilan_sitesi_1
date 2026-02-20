from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    dealer_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="stripe")
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(5), nullable=False, server_default="EUR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_payments_invoice", "invoice_id"),
        Index("ix_payments_dealer", "dealer_id"),
        Index("ix_payments_status", "status"),
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="stripe")
    session_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    dealer_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency: Mapped[str] = mapped_column(String(5), nullable=False, server_default="EUR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="unpaid")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_payment_transactions_invoice", "invoice_id"),
        Index("ix_payment_transactions_dealer", "dealer_id"),
        Index("ix_payment_transactions_status", "status"),
    )


class PaymentEventLog(Base):
    __tablename__ = "payment_event_logs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="stripe")
    event_id: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_payment_event_logs_type", "event_type"),
    )
