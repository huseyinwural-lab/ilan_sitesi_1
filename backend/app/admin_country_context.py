from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.core import Country


@dataclass
class AdminCountryContext:
    mode: str  # "global" | "country"
    country: Optional[str] = None  # country code e.g. "DE"


def _normalize_country(value: str) -> str:
    return value.strip().upper()


async def resolve_admin_country_context(
    request: Request,
    *,
    current_user: dict,
    session: Optional[AsyncSession] = None,
) -> AdminCountryContext:
    """Resolves admin mode/country from URL query params and enforces RBAC country scope.

    Rules:
    - mode is derived from presence of ?country=XX
      - absent => global
      - present => country mode
    - if country mode, validate country exists
    - RBAC enforcement:
      - super_admin (or any user with country_scope ['*']) can access any country
      - users with explicit country_scope list are restricted to those codes
    """

    raw_country = request.query_params.get("country")

    if not raw_country:
        ctx = AdminCountryContext(mode="global", country=None)
        request.state.admin_country_ctx = ctx
        return ctx

    country = _normalize_country(raw_country)

    if session is not None:
        result = await session.execute(
            select(Country).where(Country.code == country)
        )
        exists = result.scalar_one_or_none()
        if not exists or not exists.is_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid country parameter",
            )

    # RBAC scope
    scope = current_user.get("country_scope") or []
    if "*" not in scope and country not in scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Country scope forbidden",
        )

    ctx = AdminCountryContext(mode="country", country=country)
    request.state.admin_country_ctx = ctx
    return ctx
