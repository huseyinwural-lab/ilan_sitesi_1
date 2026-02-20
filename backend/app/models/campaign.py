from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import JSON
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import uuid

from app.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    country_scope: Mapped[str] = mapped_column(String(20), nullable=False, default="global")
    country_code: Mapped[Optional[str]] = mapped_column(String(5), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    target: Mapped[str] = mapped_column(String(30), nullable=False, default="discount")
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    discount_percent: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    discount_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    discount_currency: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    min_listing_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_listing_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    eligible_categories: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    eligible_user_segment: Mapped[str] = mapped_column(String(30), nullable=False, default="all")

    eligible_dealer_plan: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    eligible_dealers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    eligible_users: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    free_listing_quota_bonus: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_by_admin_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
