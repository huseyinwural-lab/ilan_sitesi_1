import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.local", override=True)

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.notification import Notification


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


def _parse_uuid(value: Any) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def _normalize_payload(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    return {"raw": value}


def _load_from_file(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("items") or data.get("notifications") or []
    if not isinstance(data, list):
        raise ValueError("Unsupported JSON format for notifications export")
    for item in data:
        if isinstance(item, dict):
            yield item


def _load_from_mongo(mongo_url: str, db_name: str, limit: Optional[int]) -> Iterable[Dict[str, Any]]:
    try:
        from pymongo import MongoClient
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("pymongo is required for Mongo backfill. Install with: pip install pymongo") from exc

    client = MongoClient(mongo_url)
    db = client[db_name]
    cursor = db.notifications.find({}, {"_id": 0})
    if limit:
        cursor = cursor.limit(limit)
    for doc in cursor:
        yield doc


def _build_notification(doc: Dict[str, Any]) -> Optional[Notification]:
    user_uuid = _parse_uuid(doc.get("user_id"))
    if not user_uuid:
        return None

    created_at = _parse_datetime(doc.get("created_at") or doc.get("createdAt"))
    read_at = _parse_datetime(doc.get("read_at") or doc.get("readAt"))
    delivered_at = _parse_datetime(doc.get("delivered_at") or doc.get("deliveredAt"))

    if doc.get("read") is True and not read_at:
        read_at = created_at or datetime.now(timezone.utc)

    payload = _normalize_payload(
        doc.get("payload_json")
        or doc.get("payload")
        or doc.get("metadata")
        or doc.get("data")
    )

    notification_id = _parse_uuid(doc.get("id")) or uuid.uuid4()
    title = doc.get("title") or doc.get("subject") or doc.get("notification_title")
    message = doc.get("message") or doc.get("body") or doc.get("text") or doc.get("content")
    if not message:
        return None

    source_type = doc.get("source_type") or doc.get("type") or doc.get("category")
    source_id = doc.get("source_id") or doc.get("listing_id") or doc.get("thread_id") or doc.get("application_id")
    action_url = doc.get("action_url") or doc.get("url") or doc.get("link")
    dedupe_key = doc.get("dedupe_key") or doc.get("idempotency_key") or doc.get("source_key")

    return Notification(
        id=notification_id,
        user_id=user_uuid,
        title=title,
        message=message,
        source_type=source_type,
        source_id=source_id,
        action_url=action_url,
        payload_json=payload,
        dedupe_key=dedupe_key,
        read_at=read_at,
        delivered_at=delivered_at,
        created_at=created_at or datetime.now(timezone.utc),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill notifications from Mongo or JSON export")
    parser.add_argument("--mongo-url", default=os.environ.get("MONGO_URL"))
    parser.add_argument("--mongo-db", default=os.environ.get("DB_NAME"))
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--source-file", type=str, default=None, help="Path to JSON export file")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report-path", type=str, default="/app/docs/notifications_backfill_report.json")

    args = parser.parse_args()

    if not args.database_url:
        raise RuntimeError("DATABASE_URL is required")

    engine = create_engine(args.database_url)
    SessionLocal = sessionmaker(bind=engine)

    if args.source_file:
        source_path = Path(args.source_file)
        if not source_path.exists():
            raise RuntimeError(f"Source file not found: {source_path}")
        source_iter = _load_from_file(source_path)
    else:
        if not args.mongo_url or not args.mongo_db:
            raise RuntimeError("MONGO_URL and DB_NAME are required for Mongo backfill")
        source_iter = _load_from_mongo(args.mongo_url, args.mongo_db, args.limit)

    migrated = 0
    skipped = 0
    errors = 0
    sample = []

    session = SessionLocal()
    try:
        for doc in source_iter:
            try:
                notification = _build_notification(doc)
                if not notification:
                    skipped += 1
                    continue

                existing = session.get(Notification, notification.id)
                if existing:
                    skipped += 1
                    continue

                if not args.dry_run:
                    session.add(notification)
                    session.commit()
                migrated += 1

                if len(sample) < 5:
                    sample.append(
                        {
                            "id": str(notification.id),
                            "user_id": str(notification.user_id),
                            "source_type": notification.source_type,
                            "created_at": notification.created_at.isoformat() if notification.created_at else None,
                        }
                    )
            except IntegrityError:
                session.rollback()
                skipped += 1
            except Exception:
                session.rollback()
                errors += 1
    finally:
        session.close()

    report = {
        "migrated_count": migrated,
        "skipped_count": skipped,
        "error_count": errors,
        "sample": sample,
        "dry_run": args.dry_run,
    }

    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
