from datetime import datetime, timezone
import uuid

from sqlalchemy import String, DateTime, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base


class VehicleTrim(Base):
    __tablename__ = "vehicle_trims"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    make_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("vehicle_makes.id"), nullable=False, index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("vehicle_models.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    source_ref: Mapped[str] = mapped_column(String(120), nullable=True, index=True)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("make_id", "model_id", "year", "slug", name="uq_vehicle_trim_identity"),
        Index("ix_vehicle_trim_source_ref", "source_ref"),
    )
