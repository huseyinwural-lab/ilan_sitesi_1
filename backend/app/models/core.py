from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid
import enum
from app.core.database import Base

class FeatureScope(str, enum.Enum):
    MODULE = "module"
    FEATURE = "feature"

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(JSON, nullable=False)  # {"tr": "...", "de": "...", "fr": "..."}
    description = Column(JSON, nullable=True)
    scope = Column(Enum(FeatureScope), default=FeatureScope.FEATURE, nullable=False)
    
    # Enabled state per country
    enabled_countries = Column(JSON, default=list)  # ['DE', 'FR', 'CH', 'AT']
    
    # Global toggle
    is_enabled = Column(Boolean, default=False)
    
    # Dependencies
    depends_on = Column(JSON, default=list)  # Other feature flag keys
    
    # Versioning
    version = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(5), unique=True, nullable=False, index=True)
    name = Column(JSON, nullable=False)  # {"tr": "...", "de": "...", "fr": "..."}
    
    # Settings
    default_currency = Column(String(5), nullable=False)  # EUR, CHF
    default_language = Column(String(5), default='de')
    
    # Locale settings
    area_unit = Column(String(10), default='m²')
    distance_unit = Column(String(10), default='km')
    weight_unit = Column(String(10), default='kg')
    date_format = Column(String(20), default='DD.MM.YYYY')
    number_format = Column(String(20), default='1.234,56')
    
    # Support info
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    
    # Status
    is_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Actor
    user_id = Column(UUID(as_uuid=True), nullable=True)
    user_email = Column(String(255), nullable=True)  # Snapshot at time of action
    
    # Action
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE, etc.
    resource_type = Column(String(100), nullable=False)  # user, feature_flag, country, etc.
    resource_id = Column(String(100), nullable=True)
    
    # Details
    old_values = Column(JSON, nullable=True)  # GDPR scrub candidate
    new_values = Column(JSON, nullable=True)  # GDPR scrub candidate
    metadata = Column(JSON, nullable=True)
    
    # Context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    country_scope = Column(String(5), nullable=True)
    
    # GDPR
    is_pii_scrubbed = Column(Boolean, default=False)
    
    # Timestamp (immutable)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
