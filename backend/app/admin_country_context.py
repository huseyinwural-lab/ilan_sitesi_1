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
    session: AsyncSession,
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

    # Validate exists
    exists = await db.countries.find_one(
        {"$or": [{"code": country}, {"country_code": country}]},
        {"_id": 0, "code": 1, "country_code": 1, "is_enabled": 1, "active_flag": 1},
    )
    if not exists or (exists.get("active_flag") is False) or (exists.get("is_enabled") is False):
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
