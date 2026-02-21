from sqlalchemy import String, Text, DateTime, Numeric, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)

    budget_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    budget_currency: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_campaigns_country_status", "country_code", "status"),
        Index("ix_campaigns_start_at", "start_at"),
        Index("ix_campaigns_end_at", "end_at"),
        Index("ix_campaigns_created_at", "created_at"),
    )
