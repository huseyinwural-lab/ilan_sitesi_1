from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Float, Integer
import uuid
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="support", nullable=False, index=True)
    user_type: Mapped[str] = mapped_column(String(20), default="individual", nullable=False, index=True)
    kyc_status: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    email_verification_code_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_verification_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verification_attempts: Mapped[int] = mapped_column(Integer, default=0)
    country_scope: Mapped[list] = mapped_column(JSON, default=list)
    preferred_language: Mapped[str] = mapped_column(String(5), default='tr')
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Country (P19)
    country_code: Mapped[str] = mapped_column(String(5), server_default="TR", nullable=False, index=True)
    device_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    # Referral (P14)
    referral_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    referred_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Referral Tier (P18)
    referral_tier_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("referral_tiers.id"), nullable=True)
    referral_count_confirmed: Mapped[int] = mapped_column(Integer, default=0)
    # Quota limits (Billing)
    listing_quota_limit: Mapped[int] = mapped_column(Integer, default=0)
    showcase_quota_limit: Mapped[int] = mapped_column(Integer, default=0)
    # Affiliate (P18)
    is_affiliate: Mapped[bool] = mapped_column(Boolean, default=False)
    referred_by_affiliate_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("affiliates.id"), nullable=True)

    def _coerce_value(self, value):
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def get(self, key, default=None):
        value = getattr(self, key, default)
        return self._coerce_value(value)

    def __getitem__(self, key):
        if not hasattr(self, key):
            raise KeyError(key)
        return self._coerce_value(getattr(self, key))

    @property
    def email_verified(self) -> bool:
        return self.is_verified

    @email_verified.setter
    def email_verified(self, value: bool) -> None:
        self.is_verified = value

    @property
    def default_country(self) -> str:
        return self.country_code

    @default_country.setter
    def default_country(self, value: str) -> None:
        if value is None:
            self.country_code = value
        else:
            self.country_code = value.upper()

class SignupAllowlist(Base):
    """Soft Launch Invite List"""
    __tablename__ = "signup_allowlist"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True) # Admin ID
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))