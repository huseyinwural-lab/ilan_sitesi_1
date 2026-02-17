from sqlalchemy import String, Boolean, DateTime, JSON, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from datetime import datetime, timezone
import uuid
from app.models.base import Base

class MLModel(Base):
    __tablename__ = "ml_models"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadata
    framework: Mapped[str] = mapped_column(String(50), default="sklearn") # xgboost, lightgbm
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default={})
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class MLPredictionLog(Base):
    __tablename__ = "ml_prediction_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    request_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True) # Optional correlation
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    
    # Metrics
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    top_score: Mapped[float] = mapped_column(Float, default=0.0)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_ml_logs_model_date', 'model_version', 'created_at'),
    )
