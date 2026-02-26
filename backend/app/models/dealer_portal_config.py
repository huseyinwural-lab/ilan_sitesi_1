from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Integer, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base


class DealerNavItem(Base):
    __tablename__ = "dealer_nav_items"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    label_i18n_key: Mapped[str] = mapped_column(String(120), nullable=False)
    route: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(60), nullable=False, default="Circle")
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    role_scope: Mapped[str] = mapped_column(String(120), nullable=False, default="dealer")
    feature_flag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location: Mapped[str] = mapped_column(String(20), nullable=False, default="sidebar")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_dealer_nav_items_location_order", "location", "order_index"),
    )


class DealerModule(Base):
    __tablename__ = "dealer_modules"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    title_i18n_key: Mapped[str] = mapped_column(String(120), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    feature_flag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    data_source_key: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_dealer_modules_order", "order_index"),
    )
