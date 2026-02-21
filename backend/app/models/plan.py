from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_scope: Mapped[str] = mapped_column(String(20), nullable=False, server_default="global")
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, server_default="monthly")
    price_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    currency_code: Mapped[str] = mapped_column(String(5), nullable=False, server_default="EUR")
    listing_quota: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    showcase_quota: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    active_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("country_scope", "country_code", "slug", "period", name="uq_plans_scope_country_slug_period"),
        Index("ix_plans_country_scope", "country_scope"),
        Index("ix_plans_country_code", "country_code"),
        Index("ix_plans_period", "period"),
        Index("ix_plans_active_flag", "active_flag"),
        Index("ix_plans_archived_at", "archived_at"),
    )
