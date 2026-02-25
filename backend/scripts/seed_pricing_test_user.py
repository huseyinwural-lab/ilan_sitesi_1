import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import select, delete
from passlib.context import CryptContext

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pricing_test_seed")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

TEST_USERS = [
    {
        "email": "pricing_individual@platform.com",
        "password": "Pricing123!",
        "full_name": "Pricing Individual",
        "role": "individual",
        "user_type": "individual",
        "country_code": "DE",
    },
    {
        "email": "pricing_corporate@platform.com",
        "password": "Pricing123!",
        "full_name": "Pricing Corporate",
        "role": "dealer",
        "user_type": "corporate",
        "country_code": "DE",
    },
]

async def seed(reset: bool = False) -> None:
    if os.environ.get("APP_ENV") == "production":
        logger.error("STOP: Cannot run seed in production")
        return

    async with AsyncSessionLocal() as session:
        for user in TEST_USERS:
            result = await session.execute(select(User).where(User.email == user["email"]))
            existing = result.scalar_one_or_none()
            if existing:
                if reset:
                    existing.hashed_password = get_password_hash(user["password"])
                    existing.full_name = user["full_name"]
                    existing.role = user["role"]
                    existing.user_type = user["user_type"]
                    existing.country_code = user["country_code"]
                    existing.is_active = True
                    existing.is_verified = True
                    existing.updated_at = datetime.now(timezone.utc)
                    logger.info("Reset user %s", user["email"])
                else:
                    logger.info("User exists %s", user["email"])
                continue

            new_user = User(
                email=user["email"],
                hashed_password=get_password_hash(user["password"]),
                full_name=user["full_name"],
                role=user["role"],
                user_type=user["user_type"],
                country_code=user["country_code"],
                is_active=True,
                is_verified=True,
                created_at=datetime.now(timezone.utc),
            )
            session.add(new_user)
            logger.info("Created user %s", user["email"])

        await session.commit()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    asyncio.run(seed(reset=reset_flag))
