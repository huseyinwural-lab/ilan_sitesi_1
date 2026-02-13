
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from datetime import datetime, timezone
import uuid
from app.models.base import Base

class VehicleMake(Base):
    __tablename__ = "vehicle_makes"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True) # ['car', 'moto']
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    source_ref: Mapped[str] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class VehicleModel(Base):
    __tablename__ = "vehicle_models"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    make_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("vehicle_makes.id"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False) # 'car', 'moto'
    year_from: Mapped[int] = mapped_column(Integer, nullable=True)
    year_to: Mapped[int] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        UniqueConstraint('make_id', 'slug', name='uq_make_model'),
    )
