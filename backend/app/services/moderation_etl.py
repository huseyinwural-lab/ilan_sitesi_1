import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import create_engine, text, select, func
from sqlalchemy.orm import sessionmaker

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


class ModerationEtlError(RuntimeError):
    def __init__(self, message: str, code: str = "ETL_ERROR") -> None:
        super().__init__(message)
        self.code = code


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
        return None
    return db[name]


def _resolve_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ModerationEtlError("DATABASE_URL is required", code="DATABASE_URL_MISSING")
    if database_url.startswith("postgresql+asyncpg"):
        database_url = database_url.replace("postgresql+asyncpg", "postgresql")
    return database_url


def _resolve_mongo_client(mongo_url: Optional[str]):
    if not mongo_url:
        raise ModerationEtlError("MONGO_URL is required", code="MONGO_URL_MISSING")
    try:
        from pymongo import MongoClient
        from pymongo.errors import ServerSelectionTimeoutError
    except Exception as exc:  # pragma: no cover
        raise ModerationEtlError("pymongo is required", code="PYMONGO_MISSING") from exc

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        raise ModerationEtlError("Mongo connection failed", code="MONGO_CONNECTION_FAILED") from exc
    return client


def run_moderation_etl(
    *,
    mongo_url: Optional[str],
    mongo_db: Optional[str],
    batch_size: int = 500,
    limit: Optional[int] = None,
    truncate: bool = False,
) -> dict:
    if not mongo_db:
        raise ModerationEtlError("DB_NAME is required", code="MONGO_DB_MISSING")

    database_url = _resolve_database_url()
    mongo_client = _resolve_mongo_client(mongo_url)
    mongo_db_obj = mongo_client[mongo_db]

    queue_collection = _get_collection(mongo_db_obj, "moderation_queue")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    if truncate:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE moderation_items"))

    inserted = 0
    skipped_missing = 0
    skipped_existing = 0
    errors = 0
    error_path = Path("/app/memory/etl_errors.log")

    existing_listing_ids: set[uuid.UUID] = set()
    with SessionLocal() as session:
        existing_rows = session.execute(select(ModerationItem.listing_id)).all()
        existing_listing_ids = {row[0] for row in existing_rows if row and row[0]}

    if queue_collection is not None:
        cursor = queue_collection.find({}, {})
        if limit:
            cursor = cursor.limit(limit)
        batch = []
        for doc in cursor:
            listing_id = _normalize_uuid(doc.get("listing_id") or doc.get("listingId") or doc.get("listing"))
            if not listing_id:
                skipped_missing += 1
                errors += 1
                _log_error(error_path, {"error": "missing_listing_id", "doc": str(doc.get("_id"))})
                continue
            if listing_id in existing_listing_ids:
                skipped_existing += 1
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
            if len(batch) >= batch_size:
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

    mongo_count = queue_collection.count_documents({}) if queue_collection is not None else 0

    state_payload = {
        "last_etl_at": datetime.now(timezone.utc).isoformat(),
        "queue_inserted": inserted,
        "queue_skipped": skipped_missing,
        "queue_errors": errors,
        "queue_skipped_existing": skipped_existing,
        "queue_collection_exists": queue_collection is not None,
        "mongo_count": mongo_count,
    }
    Path("/app/memory/MODERATION_ETL_STATE.json").write_text(json.dumps(state_payload, indent=2))
    return state_payload


def _datetime_match(left: Optional[datetime], right: Optional[datetime]) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return abs((left - right).total_seconds()) <= 1


def generate_moderation_parity_report(
    *,
    mongo_url: Optional[str],
    mongo_db: Optional[str],
    sample_size: int = 50,
) -> dict:
    if not mongo_db:
        raise ModerationEtlError("DB_NAME is required", code="MONGO_DB_MISSING")

    database_url = _resolve_database_url()
    mongo_client = _resolve_mongo_client(mongo_url)
    mongo_db_obj = mongo_client[mongo_db]
    queue_collection = _get_collection(mongo_db_obj, "moderation_queue")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        sql_count = session.execute(select(func.count()).select_from(ModerationItem)).scalar_one() or 0
        sample_rows = (
            session.execute(
                select(ModerationItem)
                .order_by(ModerationItem.created_at.desc())
                .limit(sample_size)
            )
            .scalars()
            .all()
        )

    mongo_count = queue_collection.count_documents({}) if queue_collection is not None else 0

    listing_ids = [str(row.listing_id) for row in sample_rows if row.listing_id]
    listing_uuid_values = []
    for lid in listing_ids:
        try:
            listing_uuid_values.append(uuid.UUID(lid))
        except ValueError:
            continue

    mongo_docs = []
    if queue_collection is not None and listing_ids:
        mongo_docs = list(
            queue_collection.find(
                {
                    "$or": [
                        {"listing_id": {"$in": listing_ids}},
                        {"listing_id": {"$in": listing_uuid_values}},
                        {"listingId": {"$in": listing_ids}},
                        {"listing": {"$in": listing_ids}},
                    ]
                }
            )
        )

    mongo_map = {}
    for doc in mongo_docs:
        key = doc.get("listing_id") or doc.get("listingId") or doc.get("listing")
        if key is None:
            continue
        mongo_map[str(key)] = doc

    lines = []
    lines.append("# Moderation Parity Report (Mongo vs Postgres)")
    lines.append(f"Generated at: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append(f"Mongo moderation_queue count: {mongo_count}")
    lines.append(f"SQL moderation_items count: {sql_count}")
    lines.append("")
    lines.append("## Sample Field Match (50)")
    lines.append("| Listing ID | Status Match | Reason Match | Moderator Match | Created Match | Updated Match | Mongo Status | SQL Status |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

    if not sample_rows:
        lines.append("| - | - | - | - | - | - | - | - |")
    else:
        for row in sample_rows:
            listing_id = str(row.listing_id)
            mongo_doc = mongo_map.get(listing_id)
            mongo_status = _normalize_status(mongo_doc.get("status")) if mongo_doc else None
            sql_status = _normalize_status(row.status)
            status_match = "OK" if mongo_status and mongo_status == sql_status else "NO"

            mongo_reason = _sanitize_reason(
                mongo_doc.get("reason") if mongo_doc else None
            )
            sql_reason = _sanitize_reason(row.reason)
            reason_match = "OK" if mongo_reason == sql_reason else "NO"

            mongo_moderator = _normalize_uuid(
                mongo_doc.get("moderator_id") if mongo_doc else None
            )
            sql_moderator = row.moderator_id
            moderator_match = "OK" if mongo_moderator == sql_moderator else "NO"

            mongo_created = _parse_datetime(mongo_doc.get("created_at") if mongo_doc else None)
            mongo_updated = _parse_datetime(mongo_doc.get("updated_at") if mongo_doc else None)
            created_match = "OK" if _datetime_match(mongo_created, row.created_at) else "NO"
            updated_match = "OK" if _datetime_match(mongo_updated, row.updated_at) else "NO"

            lines.append(
                "| {listing_id} | {status_match} | {reason_match} | {moderator_match} | {created_match} | {updated_match} | {mongo_status} | {sql_status} |".format(
                    listing_id=listing_id,
                    status_match=status_match,
                    reason_match=reason_match,
                    moderator_match=moderator_match,
                    created_match=created_match,
                    updated_match=updated_match,
                    mongo_status=mongo_status or "-",
                    sql_status=sql_status or "-",
                )
            )

    if queue_collection is None:
        lines.append("")
        lines.append("> Not: moderation_queue koleksiyonu bulunamadı.")
    elif mongo_count == 0:
        lines.append("")
        lines.append("> Not: moderation_queue koleksiyonu boş.")

    report_path = Path("/app/memory/MODERATION_PARITY_REPORT.md")
    report_path.write_text("
".join(lines) + "
")

    return {
        "mongo_count": mongo_count,
        "sql_count": sql_count,
        "sample_size": len(sample_rows),
        "collection_exists": queue_collection is not None,
        "report_path": str(report_path),
    }
