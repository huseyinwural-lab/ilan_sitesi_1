import asyncio
import os
import sys
import uuid
import secrets
from datetime import datetime, timezone

from sqlalchemy import select

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(ROOT_DIR)

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.core import Country
from app.core.security import get_password_hash

COUNTRIES = [
    {
        "code": "DE",
        "name": {"tr": "Almanya", "de": "Deutschland", "fr": "Allemagne"},
        "default_currency": "EUR",
        "default_language": "de",
        "support_email": "support@platform.de",
    },
    {
        "code": "CH",
        "name": {"tr": "İsviçre", "de": "Schweiz", "fr": "Suisse"},
        "default_currency": "CHF",
        "default_language": "de",
        "support_email": "support@platform.ch",
    },
    {
        "code": "FR",
        "name": {"tr": "Fransa", "de": "Frankreich", "fr": "France"},
        "default_currency": "EUR",
        "default_language": "fr",
        "support_email": "support@platform.fr",
    },
    {
        "code": "AT",
        "name": {"tr": "Avusturya", "de": "Österreich", "fr": "Autriche"},
        "default_currency": "EUR",
        "default_language": "de",
        "support_email": "support@platform.at",
    },
]

USERS = [
    {
        "email": "admin@platform.com",
        "password_env": "SEED_ADMIN_PASSWORD",
        "full_name": "System Administrator",
        "role": "super_admin",
        "country_scope": ["*"],
        "country_code": "DE",
        "preferred_language": "tr",
    },
    {
        "email": "dealer@platform.com",
        "password_env": "SEED_DEALER_PASSWORD",
        "full_name": "Dealer Demo",
        "role": "dealer",
        "country_scope": ["DE"],
        "country_code": "DE",
        "preferred_language": "tr",
    },
    {
        "email": "user@platform.com",
        "password_env": "SEED_USER_PASSWORD",
        "full_name": "Test User",
        "role": "individual",
        "country_scope": ["DE"],
        "country_code": "DE",
        "preferred_language": "tr",
    },
]


def _seed_password_from_env(key: str) -> str:
    raw = (os.environ.get(key) or "").strip()
    if raw:
        return raw
    return secrets.token_urlsafe(24)


async def seed() -> None:
    if (os.environ.get("APP_ENV") or "dev").lower() == "prod":
        raise RuntimeError("Seed script cannot run in prod")

    async with AsyncSessionLocal() as session:
        for country in COUNTRIES:
            result = await session.execute(select(Country).where(Country.code == country["code"]))
            existing = result.scalar_one_or_none()
            if not existing:
                session.add(
                    Country(
                        id=uuid.uuid4(),
                        code=country["code"],
                        name=country["name"],
                        default_currency=country["default_currency"],
                        default_language=country["default_language"],
                        support_email=country["support_email"],
                        is_enabled=True,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            else:
                existing.name = country["name"]
                existing.default_currency = country["default_currency"]
                existing.default_language = country["default_language"]
                existing.support_email = country["support_email"]
                existing.is_enabled = True
                existing.updated_at = datetime.now(timezone.utc)

        for user_data in USERS:
            result = await session.execute(select(User).where(User.email == user_data["email"]))
            existing = result.scalar_one_or_none()
            hashed = get_password_hash(_seed_password_from_env(user_data["password_env"]))
            if not existing:
                session.add(
                    User(
                        id=uuid.uuid4(),
                        email=user_data["email"],
                        hashed_password=hashed,
                        full_name=user_data["full_name"],
                        role=user_data["role"],
                        country_scope=user_data["country_scope"],
                        country_code=user_data["country_code"],
                        preferred_language=user_data["preferred_language"],
                        is_active=True,
                        is_verified=True,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            else:
                existing.hashed_password = hashed
                existing.full_name = user_data["full_name"]
                existing.role = user_data["role"]
                existing.country_scope = user_data["country_scope"]
                existing.country_code = user_data["country_code"]
                existing.preferred_language = user_data["preferred_language"]
                existing.is_active = True
                existing.is_verified = True
                existing.updated_at = datetime.now(timezone.utc)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
