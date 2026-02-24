from sqlalchemy import String, DateTime, JSON, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from datetime import datetime, timezone
import uuid

from app.models.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(140), nullable=False, index=True)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True, index=True)
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    moderation_freeze_reason: Mapped[str | None] = mapped_column(String(280), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_system_settings_key_country", "key", "country_code", unique=True),
    )
