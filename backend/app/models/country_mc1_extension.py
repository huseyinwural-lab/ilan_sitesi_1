from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

# Extension for Country Model (MC1)
# Note: P19 created 'countries' table. We extend it here.
# In reality, modifying app/models/core.py

# Added Columns:
# seo_locale: Mapped[str] = mapped_column(String(10), nullable=True) # de-DE
# legal_info: Mapped[dict] = mapped_column(JSON, default={})
# default_language: Mapped[str] = mapped_column(String(5), default="en")
