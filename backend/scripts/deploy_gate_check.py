import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]


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

    db_ssl_mode = (os.environ.get("DB_SSL_MODE") or "").lower()
    if db_ssl_mode != "require":
        print("DB_SSL_MODE must be require in prod")
        return 1

    head_revision = get_head_revision()
    if not head_revision:
        print("Unable to resolve alembic head")
        return 1

    engine = create_engine(database_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        current_revision = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_revision = current_revision.scalar()

    if current_revision != head_revision:
        print(f"Migration mismatch: db={current_revision} head={head_revision}")
        return 1

    print("Deploy gate check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
