from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PricingTierRule(Base):
    __tablename__ = "pricing_tier_rules"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope: Mapped[str] = mapped_column(String(20), default="individual", nullable=False, index=True)
    year_window: Mapped[str] = mapped_column(String(20), default="calendar_year", nullable=False)
    tier_no: Mapped[int] = mapped_column(Integer, nullable=False)
    listing_from: Mapped[int] = mapped_column(Integer, nullable=False)
    listing_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    publish_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_pricing_tier_rules_scope", "scope", "is_active"),
        Index("ix_pricing_tier_rules_tier", "scope", "tier_no"),
    )
