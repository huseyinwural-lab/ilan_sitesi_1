import argparse
import os
import sys
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / '.env')
load_dotenv(ROOT_DIR / '.env.local', override=False)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.listing_search import ListingSearch


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


def _pick_price(doc: Dict[str, Any]) -> Dict[str, Any]:
    price = doc.get('price') or {}
    if isinstance(price, dict):
        amount = price.get('amount') or price.get('value')
        currency = price.get('currency') or price.get('currency_code')
        price_type = price.get('type') or price.get('price_type')
        hourly_rate = price.get('hourly_rate')
    else:
        amount = price if isinstance(price, (int, float)) else None
        currency = doc.get('currency')
        price_type = doc.get('price_type')
        hourly_rate = doc.get('hourly_rate')
    return {
        'amount': amount,
        'currency': currency,
        'price_type': price_type,
        'hourly_rate': hourly_rate,
    }


def _build_listing_search(doc: Dict[str, Any]) -> Optional[ListingSearch]:
    listing_id = _normalize_uuid(doc.get('id') or doc.get('_id'))
    if not listing_id:
        return None

    module = doc.get('module') or (doc.get('category') or {}).get('module') or 'unknown'
    category_id = _normalize_uuid(doc.get('category_id') or (doc.get('category') or {}).get('id'))

    price_payload = _pick_price(doc)

    vehicle = doc.get('vehicle') or doc.get('vehicle_data') or {}

    return ListingSearch(
        listing_id=listing_id,
        title=doc.get('title') or '',
        description=doc.get('description'),
        module=module,
        category_id=category_id,
        country_code=(doc.get('country') or doc.get('country_code') or 'DE').upper(),
        city=doc.get('city') or (doc.get('location') or {}).get('city'),
        price_amount=price_payload.get('amount'),
        price_type=price_payload.get('price_type') or doc.get('price_type'),
        hourly_rate=price_payload.get('hourly_rate'),
        currency=price_payload.get('currency') or doc.get('currency'),
        status=doc.get('status') or 'active',
        is_premium=bool(doc.get('is_premium') or doc.get('premium')),
        is_showcase=bool(doc.get('is_showcase')),
        seller_type=doc.get('seller_type') or doc.get('user_type'),
        is_verified=doc.get('is_verified'),
        make_id=_normalize_uuid(vehicle.get('make_id') or doc.get('make_id')),
        model_id=_normalize_uuid(vehicle.get('model_id') or doc.get('model_id')),
        year=vehicle.get('year') or doc.get('year'),
        attributes=doc.get('attributes') or doc.get('details') or {},
        images=doc.get('images') or doc.get('media') or [],
        published_at=_parse_datetime(doc.get('published_at')),
        created_at=_parse_datetime(doc.get('created_at')) or datetime.now(timezone.utc),
        updated_at=_parse_datetime(doc.get('updated_at')) or datetime.now(timezone.utc),
    )


def _iter_mongo_listings(mongo_url: str, db_name: str, limit: Optional[int]) -> Iterable[Dict[str, Any]]:
    try:
        from pymongo import MongoClient
    except Exception as exc:  # pragma: no cover
        raise RuntimeError('pymongo is required for migration script') from exc

    client = MongoClient(mongo_url)
    db = client[db_name]
    cursor = db.listings.find({}, {})
    if limit:
        cursor = cursor.limit(limit)
    for doc in cursor:
        yield doc


def main() -> None:
    parser = argparse.ArgumentParser(description='Migrate Mongo listings -> listings_search (Postgres)')
    parser.add_argument('--mongo-url', default=os.environ.get('MONGO_URL'))
    parser.add_argument('--mongo-db', default=os.environ.get('DB_NAME'))
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--truncate', action='store_true')
    parser.add_argument('--batch-size', type=int, default=500)
    args = parser.parse_args()

    if not args.mongo_url or not args.mongo_db:
        raise RuntimeError('MONGO_URL and DB_NAME are required')

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL is required')
    if database_url.startswith('postgresql+asyncpg'):
        database_url = database_url.replace('postgresql+asyncpg', 'postgresql')

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)

    if args.truncate and not args.dry_run:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE listings_search"))
            conn.execute(text("TRUNCATE TABLE listings CASCADE"))

    mongo_total = None
    try:
        from pymongo import MongoClient
        mongo_client = MongoClient(args.mongo_url)
        mongo_total = mongo_client[args.mongo_db].listings.count_documents({})
    except Exception:
        mongo_total = None

    inserted = 0
    skipped = 0
    batch = []
    listing_batch = []

    insert_listing_sql = text(
        """
        INSERT INTO listings (
            id, title, description, module, category_id, country, city,
            price_type, price, hourly_rate, currency,
            user_id, dealer_id, is_dealer_listing,
            images, image_count, view_count, attributes,
            make_id, model_id,
            contact_option_phone, contact_option_message,
            status, is_premium, premium_until,
            is_showcase, showcase_expires_at,
            created_at, updated_at, published_at, expires_at
        ) VALUES (
            :id, :title, :description, :module, :category_id, :country, :city,
            :price_type, :price, :hourly_rate, :currency,
            :user_id, :dealer_id, :is_dealer_listing,
            :images, :image_count, :view_count, :attributes,
            :make_id, :model_id,
            :contact_option_phone, :contact_option_message,
            :status, :is_premium, :premium_until,
            :is_showcase, :showcase_expires_at,
            :created_at, :updated_at, :published_at, :expires_at
        ) ON CONFLICT (id) DO NOTHING
        """
    )

    for doc in _iter_mongo_listings(args.mongo_url, args.mongo_db, args.limit):
        row = _build_listing_search(doc)
        if not row:
            skipped += 1
            continue
        listing_batch.append(
            {
                "id": row.listing_id,
                "title": row.title,
                "description": row.description,
                "module": row.module,
                "category_id": row.category_id,
                "country": row.country_code,
                "city": row.city,
                "price_type": row.price_type or "FIXED",
                "price": row.price_amount,
                "hourly_rate": row.hourly_rate,
                "currency": row.currency or "EUR",
                "user_id": uuid.uuid5(DEFAULT_NAMESPACE, f"user-{row.listing_id}"),
                "dealer_id": None,
                "is_dealer_listing": False,
                "images": json.dumps(row.images or []),
                "image_count": len(row.images or []),
                "view_count": 0,
                "attributes": json.dumps(row.attributes or {}),
                "make_id": None,
                "model_id": None,
                "contact_option_phone": True,
                "contact_option_message": True,
                "status": row.status or "active",
                "is_premium": bool(row.is_premium),
                "premium_until": None,
                "is_showcase": bool(row.is_showcase),
                "showcase_expires_at": None,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "published_at": row.published_at,
                "expires_at": None,
            }
        )
        batch.append(row)
        if len(batch) >= args.batch_size:
            if args.dry_run:
                inserted += len(batch)
                batch = []
                continue
            with SessionLocal() as session:
                session.execute(insert_listing_sql, listing_batch)
                session.bulk_save_objects(batch)
                session.commit()
            inserted += len(batch)
            batch = []
            listing_batch = []

    if batch:
        if args.dry_run:
            inserted += len(batch)
        else:
            with SessionLocal() as session:
                session.execute(insert_listing_sql, listing_batch)
                session.bulk_save_objects(batch)
                session.commit()
            inserted += len(batch)

    total = inserted + skipped
    state_payload = {
        "last_etl_at": datetime.now(timezone.utc).isoformat(),
        "inserted": inserted,
        "skipped": skipped,
        "total": total,
        "mongo_total": mongo_total,
        "dry_run": args.dry_run,
    }
    etl_state_path = Path("/app/memory/SEARCH_ETL_STATE.json")
    try:
        etl_state_path.write_text(json.dumps(state_payload, indent=2))
    except Exception:
        pass

    print(f'Inserted: {inserted}, Skipped: {skipped}, DryRun: {args.dry_run}')


if __name__ == '__main__':
    main()
