from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Index, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone

from app.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    source_type = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    action_url = Column(String, nullable=True)
    payload_json = Column(JSON, nullable=True)
    dedupe_key = Column(String, nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="notifications")

    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
        Index("ix_notifications_user_read", "user_id", "read_at"),
        Index("ix_notifications_user_dedupe", "user_id", "dedupe_key", unique=True),
        Index("ix_notifications_source", "source_type", "source_id"),
    )


class UserDevice(Base):
    __tablename__ = "user_devices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

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
