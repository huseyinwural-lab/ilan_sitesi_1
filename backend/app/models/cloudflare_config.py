import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import Base


class CloudflareConfig(Base):
    __tablename__ = "cloudflare_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    account_id_last4: Mapped[str | None] = mapped_column(String(8), nullable=True)
    zone_id_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    zone_id_last4: Mapped[str | None] = mapped_column(String(8), nullable=True)
    canary_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    canary_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
