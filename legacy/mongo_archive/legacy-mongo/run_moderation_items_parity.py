import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

from dotenv import load_dotenv
import psycopg2

load_dotenv('/app/backend/.env')
load_dotenv('/app/backend/.env.local', override=False)

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
DATABASE_URL = os.environ.get('DATABASE_URL')

STATUS_MAP = {
    "pending": "PENDING",
    "pending_moderation": "PENDING",
    "approved": "APPROVED",
    "published": "APPROVED",
    "rejected": "REJECTED",
    "needs_revision": "NEEDS_REVISION",
    "needs-revision": "NEEDS_REVISION",
}


def _normalize_status(value: Optional[str]) -> str:
    if not value:
        return "PENDING"
    cleaned = str(value).strip().lower()
    if cleaned in STATUS_MAP:
        return STATUS_MAP[cleaned]
    return str(value).strip().upper() or "PENDING"


def _sanitize_reason(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    cleaned = str(value).strip()
    return cleaned or None


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


def _normalize_dt(value: Any) -> Optional[str]:
    parsed = _parse_datetime(value)
    if not parsed:
        return None
    normalized = parsed.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat()


if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL missing for moderation parity')

pymongo_available = True
try:
    from pymongo import MongoClient
except Exception:
    pymongo_available = False
    MongoClient = None
    print('pymongo not available; skipping Mongo parity')

mongo_client = MongoClient(MONGO_URL) if pymongo_available and MONGO_URL and DB_NAME else None
mongo_db = mongo_client[DB_NAME] if mongo_client and DB_NAME else None

queue_collection = None
if mongo_db is not None:
    collections = mongo_db.list_collection_names()
    if 'moderation_queue' in collections:
        queue_collection = mongo_db.moderation_queue

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM moderation_items')
queue_sql_count = cur.fetchone()[0]

queue_mongo_count = queue_collection.count_documents({}) if queue_collection is not None else 0

sample_rows = []
if queue_collection is not None:
    cursor = queue_collection.find({}, {}).limit(50)
    for doc in cursor:
        listing_id = str(doc.get('listing_id') or doc.get('listingId') or doc.get('listing') or '')
        mongo_status = _normalize_status(doc.get('status'))
        mongo_reason = _sanitize_reason(doc.get('reason') or doc.get('reason_detail') or doc.get('reason_note'))
        mongo_moderator = str(doc.get('moderator_id') or doc.get('moderatorId') or '')
        mongo_created = _normalize_dt(doc.get('created_at') or doc.get('createdAt'))
        mongo_updated = _normalize_dt(doc.get('updated_at') or doc.get('updatedAt'))

        cur.execute(
            'SELECT status, reason, moderator_id, created_at, updated_at FROM moderation_items WHERE listing_id::text=%s',
            (listing_id,),
        )
        row = cur.fetchone()
        if row:
            sql_status, sql_reason, sql_moderator, sql_created, sql_updated = row
        else:
            sql_status, sql_reason, sql_moderator, sql_created, sql_updated = None, None, None, None, None

        sql_created_norm = _normalize_dt(sql_created)
        sql_updated_norm = _normalize_dt(sql_updated)

        sample_rows.append({
            'listing_id': listing_id,
            'status_match': (sql_status or '').upper() == mongo_status,
            'reason_match': (sql_reason or None) == mongo_reason,
            'moderator_match': (str(sql_moderator) if sql_moderator else '') == mongo_moderator,
            'created_match': sql_created_norm == mongo_created,
            'updated_match': sql_updated_norm == mongo_updated,
            'mongo_status': mongo_status,
            'sql_status': sql_status,
        })

report_lines = [
    '# Moderation Parity Report (Mongo vs Postgres)',
    f'Generated at: {datetime.utcnow().isoformat()}Z',
    '',
    f'Mongo moderation_queue count: {queue_mongo_count}',
    f'SQL moderation_items count: {queue_sql_count}',
    '',
]

if not pymongo_available:
    report_lines.append('> Not: pymongo yok; Mongo parity kontrolleri atlandı.')
    report_lines.append('')

report_lines.extend([
    '## Sample Field Match (50)',
    '| Listing ID | Status Match | Reason Match | Moderator Match | Created Match | Updated Match | Mongo Status | SQL Status |',
    '| --- | --- | --- | --- | --- | --- | --- | --- |',
])

if not sample_rows:
    report_lines.append('| - | - | - | - | - | - | - | - |')
    report_lines.append('\n> Not: moderation_queue koleksiyonu bulunamadı veya boş.')
else:
    for row in sample_rows:
        report_lines.append(
            f"| {row['listing_id']} | {row['status_match']} | {row['reason_match']} | {row['moderator_match']} | {row['created_match']} | {row['updated_match']} | {row['mongo_status']} | {row['sql_status']} |"
        )

Path('/app/memory/MODERATION_PARITY_REPORT.md').write_text('\n'.join(report_lines))
print('MODERATION_PARITY_REPORT.md written')

cur.close()
conn.close()
