import os
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import ssl

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.mongo import get_mongo_client, get_db_name
from app.core.security import get_password_hash
from app.models.user import User
from app.models.application import Application

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
DB_POOL_SIZE_RAW = os.environ.get("DB_POOL_SIZE")
DB_MAX_OVERFLOW_RAW = os.environ.get("DB_MAX_OVERFLOW")
DB_SSL_MODE = os.environ.get("DB_SSL_MODE")
ENVIRONMENT = os.environ.get("ENV")

if ENVIRONMENT != "preview":
    raise RuntimeError("Seed script is preview-only (ENV=preview)")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be set")
if not DB_POOL_SIZE_RAW or not DB_MAX_OVERFLOW_RAW or not DB_SSL_MODE:
    raise RuntimeError("DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_SSL_MODE must be set")
if DB_SSL_MODE != "require":
    raise RuntimeError("DB_SSL_MODE must be require")

try:
    DB_POOL_SIZE = int(DB_POOL_SIZE_RAW)
    DB_MAX_OVERFLOW = int(DB_MAX_OVERFLOW_RAW)
except ValueError as exc:
    raise RuntimeError("DB_POOL_SIZE and DB_MAX_OVERFLOW must be integers") from exc

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

sql_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    connect_args={"ssl": ssl_context},
)
AsyncSessionLocal = async_sessionmaker(
    sql_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def ensure_mongo_user(db, email: str, role: str, full_name: str, company_name: str | None = None):
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        return existing

    user_id = str(uuid.uuid4())
    payload = {
        "id": user_id,
        "email": email,
        "hashed_password": get_password_hash("Seed123!"),
        "full_name": full_name,
        "role": role,
        "status": "active",
        "is_active": True,
        "is_verified": True,
        "country_scope": ["DE"],
        "country_code": "DE",
        "preferred_language": "tr",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None,
    }
    if company_name:
        payload["company_name"] = company_name

    await db.users.insert_one(payload)
    return payload


async def ensure_sql_user(session: AsyncSession, user_doc: dict) -> uuid.UUID:
    user_uuid = uuid.UUID(str(user_doc.get("id")))
    result = await session.execute(select(User).where(User.id == user_uuid))
    existing = result.scalar_one_or_none()
    if existing:
        return user_uuid

    new_user = User(
        id=user_uuid,
        email=user_doc.get("email"),
        hashed_password=user_doc.get("hashed_password") or get_password_hash("Seed123!"),
        full_name=user_doc.get("full_name") or user_doc.get("email"),
        role=user_doc.get("role") or "individual",
        is_active=True,
        is_verified=True,
        country_scope=user_doc.get("country_scope") or ["DE"],
        preferred_language=user_doc.get("preferred_language", "tr"),
        country_code=user_doc.get("country_code", "DE"),
    )
    session.add(new_user)
    await session.flush()
    return user_uuid


async def seed_applications():
    mongo_client = get_mongo_client()
    mongo_db = mongo_client[get_db_name()]

    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)

        individual_users = []
        for idx in range(5):
            user = await ensure_mongo_user(
                mongo_db,
                email=f"seed.individual{idx+1}@platform.com",
                role="individual",
                full_name=f"Seed Individual {idx+1}",
            )
            individual_users.append(user)

        dealer_users = []
        for idx in range(5):
            user = await ensure_mongo_user(
                mongo_db,
                email=f"seed.dealer{idx+1}@platform.com",
                role="dealer",
                full_name=f"Seed Dealer {idx+1}",
                company_name=f"Seed Dealer Co {idx+1}",
            )
            dealer_users.append(user)

        seed_rows = []
        for idx, user in enumerate(individual_users):
            user_uuid = await ensure_sql_user(session, user)
            app_uuid = uuid.uuid4()
            seed_rows.append(
                Application(
                    id=app_uuid,
                    application_id=str(app_uuid),
                    user_id=user_uuid,
                    application_type="individual",
                    category="complaint" if idx % 2 == 0 else "request",
                    subject=f"Bireysel Başvuru {idx+1}",
                    description="Seed açıklama (bireysel)",
                    attachments=[],
                    extra_data={"kvkk_consent": True},
                    priority="medium",
                    status="pending" if idx % 2 == 0 else "in_review",
                    created_at=now - timedelta(days=idx),
                    updated_at=now - timedelta(days=idx),
                )
            )

        for idx, user in enumerate(dealer_users):
            user_uuid = await ensure_sql_user(session, user)
            app_uuid = uuid.uuid4()
            seed_rows.append(
                Application(
                    id=app_uuid,
                    application_id=str(app_uuid),
                    user_id=user_uuid,
                    application_type="dealer",
                    category="complaint" if idx % 2 == 0 else "request",
                    subject=f"Kurumsal Başvuru {idx+1}",
                    description="Seed açıklama (kurumsal)",
                    attachments=[],
                    extra_data={"company_name": user.get("company_name"), "kvkk_consent": True},
                    priority="medium",
                    status="pending" if idx % 2 == 0 else "in_review",
                    created_at=now - timedelta(days=idx),
                    updated_at=now - timedelta(days=idx),
                )
            )

        session.add_all(seed_rows)
        await session.commit()

    mongo_client.close()


if __name__ == "__main__":
    asyncio.run(seed_applications())
