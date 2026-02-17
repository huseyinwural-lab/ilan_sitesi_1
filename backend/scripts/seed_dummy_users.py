
import asyncio
import logging
import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.user import User

# Security Helper (Copied to avoid import loop or path issues)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dummy_seed")

# CONFIG
COUNT_INDIVIDUAL = 20
COUNTRIES = ["DE", "TR", "FR"]

async def seed_dummy_data():
    # Safety Guard
    if os.environ.get("APP_ENV") == "production":
        logger.error("🚫 STOP: Cannot run seed in PRODUCTION!")
        return

    logger.info("🌱 Starting Dummy Data Seed (Users Only)...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Cleanup
            logger.info("Cleaning old dummy users...")
            await session.execute(delete(User).where(User.email.like("user_%@example.com")))
            await session.commit()

            # 2. Users (Individual)
            users = []
            for i in range(COUNT_INDIVIDUAL):
                country = random.choices(COUNTRIES, weights=[50, 30, 20])[0]
                user = User(
                    email=f"user_{i}@example.com",
                    hashed_password=get_password_hash("password"),
                    full_name=f"Test User {i}",
                    role="individual",
                    country_scope=[country],
                    is_active=True,
                    is_verified=random.random() < 0.7,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))
                )
                session.add(user)
                users.append(user)
            
            await session.commit()
            logger.info(f"✅ Created {len(users)} Individual Users")
            logger.info("🎉 Seed Complete!")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_dummy_data())
