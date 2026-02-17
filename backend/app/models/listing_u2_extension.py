from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
# Extension for Listing Model (U2)
# In reality, this modifies app/models/moderation.py Listing class.

# Added Columns:
# current_step: Mapped[int] = mapped_column(Integer, default=1)
# completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
# user_type_snapshot: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
# last_edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
# moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
# moderated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
# rejected_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
# deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
