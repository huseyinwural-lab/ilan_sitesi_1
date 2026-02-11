from sqlalchemy import Column, String, Boolean, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    COUNTRY_ADMIN = "country_admin"
    MODERATOR = "moderator"
    SUPPORT = "support"
    FINANCE = "finance"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.SUPPORT, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Multi-country scope
    country_scope = Column(JSON, default=list)  # ['DE', 'FR'] or ['*'] for all
    
    # Preferences
    preferred_language = Column(String(5), default='tr')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # 2FA (flag for future)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
