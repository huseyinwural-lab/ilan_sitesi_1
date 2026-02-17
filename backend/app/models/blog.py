
"""
P18: Blog Module Models
"""
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from datetime import datetime, timezone
from typing import Optional
import uuid
from app.models.base import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Short description
    body_html: Mapped[str] = mapped_column(Text, nullable=False) # Main content
    cover_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Meta
    author: Mapped[str] = mapped_column(String(100), default="Platform Team")
    tags: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Comma separated for MVP
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # SEO
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
