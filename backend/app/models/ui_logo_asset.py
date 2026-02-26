from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UILogoAsset(Base):
    __tablename__ = "ui_logo_assets"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    asset_url: Mapped[str] = mapped_column(String(512), nullable=False)

    segment: Mapped[str] = mapped_column(String(16), nullable=False, default="corporate", index=True)
    scope: Mapped[str] = mapped_column(String(16), nullable=False, default="system", index=True)
    scope_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    config_type: Mapped[str] = mapped_column(String(16), nullable=False, default="header", index=True)

    is_replaced: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    replaced_by_asset_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    replaced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delete_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_ui_logo_assets_scope_lookup", "config_type", "segment", "scope", "scope_id"),
    )
