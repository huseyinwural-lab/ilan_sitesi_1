import asyncio
import os

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from server import (
    _ensure_admin_user,
    _ensure_dealer_user,
    _ensure_test_user,
    _ensure_test_user_two,
    _ensure_individual_fixtures,
    _ensure_country_admin_user,
)


async def seed_manual_fixtures() -> None:
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Manual fixture seeding is disabled in production")

    if (os.environ.get("ALLOW_MANUAL_FIXTURE_SEED") or "").strip().lower() not in {"1", "true", "yes"}:
        raise RuntimeError("Set ALLOW_MANUAL_FIXTURE_SEED=true to run fixture seeding")

    async with AsyncSessionLocal() as session:
        await _ensure_admin_user(session)
        await _ensure_dealer_user(session)
        await _ensure_test_user(session)
        await _ensure_test_user_two(session)
        await _ensure_individual_fixtures(session)
        await _ensure_country_admin_user(session)


if __name__ == "__main__":
    asyncio.run(seed_manual_fixtures())
