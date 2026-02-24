import logging
import os
import ssl
import urllib.parse
from typing import Any, Dict, Optional

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

APP_ENV = settings.APP_ENV
RAW_DATABASE_URL = settings.DATABASE_URL
if not RAW_DATABASE_URL:
    raise RuntimeError("CONFIG_MISSING: DATABASE_URL")

DB_POOL_SIZE_RAW = os.environ.get("DB_POOL_SIZE")
DB_MAX_OVERFLOW_RAW = os.environ.get("DB_MAX_OVERFLOW")
DB_POOL_TIMEOUT_RAW = os.environ.get("DB_POOL_TIMEOUT")
DB_POOL_RECYCLE_RAW = os.environ.get("DB_POOL_RECYCLE")
DB_POOL_DEBUG = os.environ.get("DB_POOL_DEBUG", "").lower() in {"1", "true", "yes"}
DB_SSL_MODE = (os.environ.get("DB_SSL_MODE") or ("require" if APP_ENV in {"prod", "preview"} else "disable")).lower()


def _db_url_is_localhost(value: Optional[str]) -> bool:
    if not value:
        return True
    try:
        parsed = urllib.parse.urlparse(value)
        host = (parsed.hostname or "").lower()
    except Exception:
        host = value.lower()
    return host in {"localhost", "127.0.0.1"}


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


if APP_ENV in {"preview", "prod"}:
    if _db_url_is_localhost(RAW_DATABASE_URL):
        raise RuntimeError("CONFIG_MISSING: DATABASE_URL")
    if DB_SSL_MODE != "require":
        raise RuntimeError("DB_SSL_MODE must be require for preview/prod")


def _ensure_logger(name: str, level: int) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level)
    return logger


sql_logger = _ensure_logger("sql_config", logging.INFO)
pool_logger = _ensure_logger("database.pool", logging.DEBUG if DB_POOL_DEBUG else logging.INFO)

try:
    DB_POOL_SIZE = int(DB_POOL_SIZE_RAW) if DB_POOL_SIZE_RAW else 5
    DB_MAX_OVERFLOW = int(DB_MAX_OVERFLOW_RAW) if DB_MAX_OVERFLOW_RAW else 10
    DB_POOL_TIMEOUT = int(DB_POOL_TIMEOUT_RAW) if DB_POOL_TIMEOUT_RAW else 30
    DB_POOL_RECYCLE = int(DB_POOL_RECYCLE_RAW) if DB_POOL_RECYCLE_RAW else 1800
except ValueError:
    sql_logger.warning("Invalid DB pool values, defaulting to 5/10/30/1800")
    DB_POOL_SIZE = 5
    DB_MAX_OVERFLOW = 10
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 1800

ssl_context = None
connect_args: Dict[str, Any] = {
    "server_settings": {
        "client_encoding": "UTF8",
    }
}
if DB_SSL_MODE == "require":
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

SAFE_DATABASE_URL = _sanitize_database_url(RAW_DATABASE_URL)
ASYNC_DATABASE_URL = SAFE_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args=connect_args,
)

sql_logger.info(
    "Effective DB pool config (core): pool_size=%s max_overflow=%s pool_timeout=%s pool_recycle=%s pool_pre_ping=%s",
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
    True,
)

if DB_POOL_DEBUG:
    pool_logger.setLevel(logging.DEBUG)


@event.listens_for(engine.sync_engine, "connect")
def _log_pool_connect(dbapi_connection, connection_record):
    if DB_POOL_DEBUG:
        pool_logger.debug("db_pool_connect")


@event.listens_for(engine.sync_engine, "checkout")
def _log_pool_checkout(dbapi_connection, connection_record, connection_proxy):
    if DB_POOL_DEBUG:
        pool_logger.debug("db_pool_checkout")


@event.listens_for(engine.sync_engine, "checkin")
def _log_pool_checkin(dbapi_connection, connection_record):
    if DB_POOL_DEBUG:
        pool_logger.debug("db_pool_checkin")


@event.listens_for(engine.sync_engine, "close")
def _log_pool_close(dbapi_connection, connection_record):
    if DB_POOL_DEBUG:
        pool_logger.debug("db_pool_close")


@event.listens_for(engine.sync_engine, "invalidate")
def _log_pool_invalidate(dbapi_connection, connection_record, exception):
    pool_logger.info("db_pool_invalidate", extra={"error": str(exception) if exception else None})


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
