from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.models.base import Base

class UserDevice(Base):
    __tablename__ = "user_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    token = Column(String, nullable=False, unique=True) # FCM Token
    platform = Column(String, nullable=False) # 'ios', 'android'
    device_id = Column(String, nullable=True) # Unique Hardware ID
    
    is_active = Column(Boolean, default=True)
    is_rooted = Column(Boolean, default=False) # Security Flag
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="devices")

    __table_args__ = (
        Index('idx_user_device_token', 'token'),
        Index('idx_user_device_user', 'user_id'),
    )
