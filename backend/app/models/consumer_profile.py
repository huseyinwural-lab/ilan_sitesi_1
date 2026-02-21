from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base


class ConsumerProfile(Base):
    __tablename__ = "consumer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)

    language: Mapped[str] = mapped_column(String(10), default="tr")
    country_code: Mapped[str] = mapped_column(String(5), default="DE")
    display_name_mode: Mapped[str] = mapped_column(String(30), default="full_name")
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False)

    gdpr_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    totp_recovery_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_consumer_profiles_user", "user_id"),
    )
