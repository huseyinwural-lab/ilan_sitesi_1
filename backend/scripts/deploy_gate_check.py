import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]


def mask_target(database_url: str) -> dict:
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown"
    db_name = parsed.path.lstrip("/") if parsed.path else ""

    if host not in {"localhost", "127.0.0.1"}:
        parts = host.split(".")
        if len(parts) > 2:
            host = ".".join(parts[-2:])

    masked_db = f"{db_name[:3]}***" if db_name else "unknown"
    return {"host": host, "database": masked_db}


def get_head_revision() -> str | None:
    alembic_cfg = Config(str(ROOT_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(alembic_cfg)
    return script.get_current_head()


def main() -> int:
    app_env = (os.environ.get("APP_ENV") or "dev").lower()
    if app_env != "prod":
        print("APP_ENV is not prod; deploy gate skipped")
        return 0

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL is required for prod")
        return 1

    parsed = urlparse(database_url)
    if parsed.hostname in {"localhost", "127.0.0.1"}:
        print("DATABASE_URL must not point to localhost in prod")
        return 1
    if "admin_user" in database_url or "admin_pass" in database_url:
        print("DATABASE_URL appears to be placeholder")
        return 1

    db_ssl_mode = (os.environ.get("DB_SSL_MODE") or "").lower()
    if db_ssl_mode != "require":
        print("DB_SSL_MODE must be require in prod")
        return 1

    head_revision = get_head_revision()
    if not head_revision:
        print("Unable to resolve alembic head")
        return 1

    target = mask_target(database_url)
    print(f"DB target host={target['host']} db={target['database']}")

    engine = create_engine(database_url)
    last_exc = None
    for attempt in range(3):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                current_revision = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_revision = current_revision.scalar()
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(2)
    else:
        print(f"Database connection failed: {last_exc}")
        return 1

    print(f"Migration check: db={current_revision} head={head_revision}")
    if current_revision != head_revision:
        print("Migration mismatch")
        return 1

    print("Deploy gate check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
