import argparse
import os
import sys
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / '.env')
load_dotenv(ROOT_DIR / '.env.local', override=False)

from app.models.moderation import ModerationQueue, ModerationAction

DEFAULT_NAMESPACE = uuid.UUID('00000000-0000-0000-0000-000000000000')


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, dict) and '$date' in value:
        return _parse_datetime(value.get('$date'))
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            cleaned = cleaned.replace('Z', '+00:00')
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
        return uuid.uuid5(DEFAULT_NAMESPACE, str(value))


def _get_collection(db, name: str):
    if db is None:
        return None
    collections = db.list_collection_names()
    if name not in collections:
        print(f"Collection not found: {name}")
        return None
    return db[name]


def main() -> None:
    parser = argparse.ArgumentParser(description='Migrate moderation_queue + moderation_audit to SQL')
    parser.add_argument('--mongo-url', default=os.environ.get('MONGO_URL'))
    parser.add_argument('--mongo-db', default=os.environ.get('DB_NAME'))
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--batch-size', type=int, default=500)
    parser.add_argument('--truncate', action='store_true')
    args = parser.parse_args()

    if not args.mongo_url or not args.mongo_db:
        raise RuntimeError('MONGO_URL and DB_NAME are required')

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL is required')
    if database_url.startswith('postgresql+asyncpg'):
        database_url = database_url.replace('postgresql+asyncpg', 'postgresql')

    try:
        from pymongo import MongoClient
    except Exception as exc:
        raise RuntimeError('pymongo is required for moderation migration') from exc

    mongo_client = MongoClient(args.mongo_url)
    mongo_db = mongo_client[args.mongo_db]

    queue_collection = _get_collection(mongo_db, 'moderation_queue')
    audit_collection = _get_collection(mongo_db, 'moderation_audit')

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    if args.truncate:
        with engine.begin() as conn:
            conn.execute(text('TRUNCATE TABLE moderation_queue'))
            conn.execute(text('TRUNCATE TABLE moderation_actions'))

    queue_inserted = 0
    queue_skipped = 0
    audit_inserted = 0
    audit_skipped = 0

    if queue_collection is not None:
        cursor = queue_collection.find({}, {})
        if args.limit:
            cursor = cursor.limit(args.limit)
        batch = []
        for doc in cursor:
            listing_id = _normalize_uuid(doc.get('listing_id') or doc.get('listingId') or doc.get('listing'))
            if not listing_id:
                queue_skipped += 1
                continue
            queue_id = _normalize_uuid(doc.get('id') or doc.get('_id')) or uuid.uuid4()
            batch.append(
                ModerationQueue(
                    id=queue_id,
                    listing_id=listing_id,
                    status=doc.get('status') or 'pending',
                    reason=doc.get('reason') or doc.get('reason_detail') or doc.get('reason_note'),
                    moderator_id=_normalize_uuid(doc.get('moderator_id') or doc.get('moderatorId')),
                    created_at=_parse_datetime(doc.get('created_at')) or datetime.now(timezone.utc),
                    updated_at=_parse_datetime(doc.get('updated_at')) or datetime.now(timezone.utc),
                    decided_at=_parse_datetime(doc.get('decided_at')) or _parse_datetime(doc.get('resolved_at')),
                )
            )
            if len(batch) >= args.batch_size:
                with SessionLocal() as session:
                    session.bulk_save_objects(batch)
                    session.commit()
                queue_inserted += len(batch)
                batch = []
        if batch:
            with SessionLocal() as session:
                session.bulk_save_objects(batch)
                session.commit()
            queue_inserted += len(batch)

    if audit_collection is not None:
        cursor = audit_collection.find({}, {})
        if args.limit:
            cursor = cursor.limit(args.limit)
        batch = []
        for doc in cursor:
            listing_id = _normalize_uuid(doc.get('listing_id') or doc.get('listingId') or doc.get('listing'))
            if not listing_id:
                audit_skipped += 1
                continue
            action_id = _normalize_uuid(doc.get('id') or doc.get('_id')) or uuid.uuid4()
            actor_id = _normalize_uuid(doc.get('moderator_id') or doc.get('actor_id') or doc.get('moderatorId'))
            if actor_id is None:
                actor_id = uuid.uuid5(DEFAULT_NAMESPACE, f"moderator-{listing_id}")
            batch.append(
                ModerationAction(
                    id=action_id,
                    listing_id=listing_id,
                    action_type=doc.get('action') or doc.get('action_type') or 'unknown',
                    reason=doc.get('reason') or doc.get('reason_detail') or doc.get('reason_note'),
                    note=doc.get('note'),
                    actor_admin_id=actor_id,
                    actor_email=doc.get('moderator_email') or doc.get('actor_email'),
                    created_at=_parse_datetime(doc.get('created_at')) or datetime.now(timezone.utc),
                )
            )
            if len(batch) >= args.batch_size:
                with SessionLocal() as session:
                    session.bulk_save_objects(batch)
                    session.commit()
                audit_inserted += len(batch)
                batch = []
        if batch:
            with SessionLocal() as session:
                session.bulk_save_objects(batch)
                session.commit()
            audit_inserted += len(batch)

    state_payload = {
        "last_etl_at": datetime.now(timezone.utc).isoformat(),
        "queue_inserted": queue_inserted,
        "queue_skipped": queue_skipped,
        "audit_inserted": audit_inserted,
        "audit_skipped": audit_skipped,
        "queue_collection_exists": queue_collection is not None,
        "audit_collection_exists": audit_collection is not None,
    }
    Path('/app/memory/MODERATION_ETL_STATE.json').write_text(json.dumps(state_payload, indent=2))
    print(json.dumps(state_payload, indent=2))


if __name__ == '__main__':
    main()
