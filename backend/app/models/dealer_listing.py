from datetime import datetime, timezone
import uuid

from sqlalchemy import String, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import Base


class DealerListing(Base):
    __tablename__ = "dealer_listings"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dealer_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
