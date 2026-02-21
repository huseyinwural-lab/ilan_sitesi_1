from sqlalchemy import String, DateTime, Boolean, JSON, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class WebhookEventLog(Base):
    __tablename__ = "webhook_event_logs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), nullable=False, server_default="stripe")
    event_id: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="received")
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    signature_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    error_message: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_webhook_event_provider_event"),
        Index("ix_webhook_event_created", "created_at"),
        Index("ix_webhook_event_status", "status"),
    )
