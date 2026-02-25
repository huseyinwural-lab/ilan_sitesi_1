from datetime import datetime, timezone
import uuid

from sqlalchemy import String, DateTime, Numeric, Integer, JSON, Index, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PricingPriceSnapshot(Base):
    __tablename__ = "pricing_price_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("listings.id"), nullable=False, unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pricing_tier_rules.id"), nullable=True)
    package_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pricing_packages.id"), nullable=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pricing_campaigns.id"), nullable=True)
    campaign_item_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pricing_campaign_items.id"), nullable=True)
    listing_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    publish_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    campaign_override_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    snapshot_type: Mapped[str] = mapped_column(String(20), nullable=False)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_pricing_snapshot_user", "user_id"),
    )
