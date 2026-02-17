
"""
P18: Affiliate System Models
"""
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Index, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class Affiliate(Base):
    __tablename__ = "affiliates"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    custom_slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    commission_rate: Mapped[Numeric] = mapped_column(Numeric(4, 2), default=0.20) # 0.20 = 20%
    
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True) # pending, approved, rejected, suspended
    
    # Store payout details (IBAN etc) as JSON or String? 
    # For MVP simplicity, just a text field or JSON if supported.
    # Let's use simple text for IBAN or JSON for flexibility.
    risk_score: Mapped[int] = mapped_column(Integer, default=0) # 0-100, >80 blocked
    # Alembic/Postgres supports JSON.
    payout_details: Mapped[Optional[dict]] = mapped_column(String, nullable=True) # JSON serialized
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("affiliates.id"), nullable=False, index=True)
    
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        # Optional: Index for analytics query
        Index('ix_affiliate_clicks_date', 'affiliate_id', 'created_at'),
    )
