from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, Index, Computed
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ListingSearch(Base):
    __tablename__ = "listings_search"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)

    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    price_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    price_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_showcase: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    seller_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_verified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    make_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    model_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    images: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    tsv_tr: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('turkish', coalesce(title, '') || ' ' || coalesce(description, ''))", persisted=True),
    )
    tsv_de: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('german', coalesce(title, '') || ' ' || coalesce(description, ''))", persisted=True),
    )

    __table_args__ = (
        Index("ix_listings_search_tsv_tr", "tsv_tr", postgresql_using="gin"),
        Index("ix_listings_search_tsv_de", "tsv_de", postgresql_using="gin"),
        Index("ix_listings_search_core", "status", "country_code", "module", "published_at"),
        Index("ix_listings_search_category_price", "category_id", "price_amount"),
        Index("ix_listings_search_make_model_year", "make_id", "model_id", "year"),
        Index("ix_listings_search_seller", "seller_type", "is_verified", "published_at"),
        Index("ix_listings_search_attrs_gin", "attributes", postgresql_using="gin"),
    )
