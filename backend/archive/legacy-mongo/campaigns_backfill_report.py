import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.local", override=True)

DATABASE_URL = os.environ.get("DATABASE_URL")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

report = {
    "sql_count": 0,
    "mongo_count": None,
    "mongo_error": None,
}

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    report["sql_count"] = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar() or 0

if MONGO_URL and DB_NAME:
    try:
        from pymongo import MongoClient

        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        report["mongo_count"] = db.campaigns.count_documents({})
    except Exception as exc:
        report["mongo_error"] = str(exc)

Path("/app/docs/campaigns_backfill_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
