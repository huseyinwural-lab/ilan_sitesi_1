import argparse
import os
import sys
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.local", override=False)

from app.models.moderation import ModerationItem

SYSTEM_MODERATOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
MAX_REASON_LEN = 500
STATUS_MAP = {
    "pending": "PENDING",
    "pending_moderation": "PENDING",
    "approved": "APPROVED",
    "published": "APPROVED",
    "rejected": "REJECTED",
    "needs_revision": "NEEDS_REVISION",
    "needs-revision": "NEEDS_REVISION",
}


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, dict) and "$date" in value:
        return _parse_datetime(value.get("$date"))
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            cleaned = cleaned.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(cleaned)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _normalize_uuid(value: Any) -> Optional[uuid.UUID]:
    if value is None:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _normalize_status(value: Any) -> str:
    if not value:
        return "PENDING"
    cleaned = str(value).strip().lower()
    if cleaned in STATUS_MAP:
        return STATUS_MAP[cleaned]
    upper = str(value).strip().upper()
    return upper or "PENDING"


def _sanitize_reason(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_REASON_LEN:
        cleaned = cleaned[:MAX_REASON_LEN]
    return cleaned


def _log_error(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _get_collection(db, name: str):
    if db is None:
        return None
    collections = db.list_collection_names()
    if name not in collections:
        print(f"Collection not found: {name}")
        return None
    return db[name]


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate moderation_queue to moderation_items")
    parser.add_argument("--mongo-url", default=os.environ.get("MONGO_URL"))
    parser.add_argument("--mongo-db", default=os.environ.get("DB_NAME"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--truncate", action="store_true")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")
    if database_url.startswith("postgresql+asyncpg"):
        database_url = database_url.replace("postgresql+asyncpg", "postgresql")

    mongo_client = None
    mongo_db = None
    pymongo_available = True
    try:
        from pymongo import MongoClient
    except Exception:
        pymongo_available = False
        MongoClient = None
        print("pymongo not available; skipping Mongo ETL")

    if pymongo_available and args.mongo_url and args.mongo_db:
        mongo_client = MongoClient(args.mongo_url)
        mongo_db = mongo_client[args.mongo_db]

    queue_collection = _get_collection(mongo_db, "moderation_queue") if mongo_db is not None else None

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    if args.truncate:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE moderation_items"))

    inserted = 0
    skipped = 0
    errors = 0
    error_path = Path("/app/memory/etl_errors.log")

    if queue_collection is not None:
        cursor = queue_collection.find({}, {})
        if args.limit:
            cursor = cursor.limit(args.limit)
        batch = []
        for doc in cursor:
            listing_id = _normalize_uuid(doc.get("listing_id") or doc.get("listingId") or doc.get("listing"))
            if not listing_id:
                skipped += 1
                errors += 1
                _log_error(error_path, {"error": "missing_listing_id", "doc": str(doc.get("_id"))})
                continue
            item_id = _normalize_uuid(doc.get("id") or doc.get("_id")) or uuid.uuid4()
            status = _normalize_status(doc.get("status"))
            reason = _sanitize_reason(doc.get("reason") or doc.get("reason_detail") or doc.get("reason_note"))
            moderator_id = _normalize_uuid(doc.get("moderator_id") or doc.get("moderatorId")) or SYSTEM_MODERATOR_ID
            audit_ref = doc.get("audit_ref") or doc.get("auditRef") or doc.get("audit_id")
            created_at = _parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc)
            updated_at = _parse_datetime(doc.get("updated_at")) or datetime.now(timezone.utc)

            batch.append(
                ModerationItem(
                    id=item_id,
                    listing_id=listing_id,
                    status=status,
                    reason=reason,
                    moderator_id=moderator_id,
                    audit_ref=str(audit_ref) if audit_ref else None,
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )
            if len(batch) >= args.batch_size:
                with SessionLocal() as session:
                    session.bulk_save_objects(batch)
                    session.commit()
                inserted += len(batch)
                batch = []

        if batch:
            with SessionLocal() as session:
                session.bulk_save_objects(batch)
                session.commit()
            inserted += len(batch)

    state_payload = {
        "last_etl_at": datetime.now(timezone.utc).isoformat(),
        "queue_inserted": inserted,
        "queue_skipped": skipped,
        "queue_errors": errors,
        "queue_collection_exists": queue_collection is not None,
        "pymongo_available": pymongo_available,
    }
    Path("/app/memory/MODERATION_ETL_STATE.json").write_text(json.dumps(state_payload, indent=2))
    print(json.dumps(state_payload, indent=2))


if __name__ == "__main__":
    main()
