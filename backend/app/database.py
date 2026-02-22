
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path
import urllib.parse

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')
load_dotenv(ROOT_DIR / '.env.local', override=False)

APP_ENV = (os.environ.get("APP_ENV") or "dev").lower()
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("CONFIG_MISSING: DATABASE_URL")
if APP_ENV in {"preview", "prod"}:
    lowered = DATABASE_URL.lower()
    if "localhost" in lowered or "127.0.0.1" in lowered:
        raise RuntimeError("CONFIG_MISSING: DATABASE_URL")
def _sanitize_database_url(value: str) -> str:
    try:
        parsed = urllib.parse.urlparse(value)
        if not parsed.query:
            return value
        params = urllib.parse.parse_qs(parsed.query)
        params.pop("sslmode", None)
        new_query = urllib.parse.urlencode(params, doseq=True)
        return parsed._replace(query=new_query).geturl()
    except Exception:
        return value


ASYNC_DATABASE_URL = _sanitize_database_url(DATABASE_URL).replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
