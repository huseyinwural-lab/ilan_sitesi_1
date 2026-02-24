from datetime import datetime, timezone
import uuid
from sqlalchemy import String, DateTime, Boolean, Index, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class InfoPage(Base):
    __tablename__ = "info_pages"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    title_tr: Mapped[str] = mapped_column(String(200), nullable=False)
    title_de: Mapped[str] = mapped_column(String(200), nullable=False)
    title_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    content_tr: Mapped[str] = mapped_column(Text, nullable=False)
    content_de: Mapped[str] = mapped_column(Text, nullable=False)
    content_fr: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_info_pages_published", "is_published"),
    )
