from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base


class UIConfig(Base):
    __tablename__ = "ui_configs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", index=True)
    segment: Mapped[str] = mapped_column(String(16), nullable=False, default="individual", index=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False, default="system", index=True)
    scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    config_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "config_type",
            "segment",
            "scope",
            "scope_id",
            "version",
            name="uq_ui_configs_version_scope",
        ),
        Index("ix_ui_configs_effective_lookup", "config_type", "segment", "scope", "scope_id", "status", "version"),
    )
