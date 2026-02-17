from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Note: This is an extension logic. In reality, we edit app/models/user.py
# But for clarity in this task context, we define what fields are added.
# See USER_MIGRATION_PLAN_U1.md

# Added to User class:
# kyc_status: Mapped[str] = mapped_column(String(20), default='none')
# default_country: Mapped[str] = mapped_column(String(5), default='DE')
# email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
# phone_verified: Mapped[bool] = mapped_column(Boolean, default=False) 
# (Note: is_phone_verified might exist from P27, we standardize to phone_verified or alias it)
