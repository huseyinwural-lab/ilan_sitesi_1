from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
import uuid
from app.models.base import Base

class LegalConsent(Base):
    __tablename__ = "legal_consents"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    country_code: Mapped[str] = mapped_column(String(5), nullable=False) # DE, FR...
    document_type: Mapped[str] = mapped_column(String(50), nullable=False) # terms, privacy
    version: Mapped[str] = mapped_column(String(20), nullable=False) # v1.0
    
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(255), nullable=True)
    
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_legal_consent_user_doc', 'user_id', 'document_type'),
    )
