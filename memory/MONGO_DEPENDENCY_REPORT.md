# Mongo Dependency Report

## Status
- pymongo: removed from runtime requirements
- Mongo scripts archived: /app/legacy/mongo_archive/legacy-mongo
- Runtime Mongo bağlantısı: devre dışı (app.state.mongo_enabled = False)

## Occurrences (rg -n "mongo")
```
/app/backend/server.py:1606:    app.state.mongo_enabled = False
/app/backend/server.py:17089:            "db_status": "mongo_disabled",
/app/legacy/mongo_archive/legacy-mongo/campaigns_backfill_report.py:20:    "mongo_count": None
/app/legacy/mongo_archive/legacy-mongo/campaigns_backfill_report.py:21:    "mongo_error": None
/app/legacy/mongo_archive/legacy-mongo/campaigns_backfill_report.py:33:        from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/campaigns_backfill_report.py:37:        report["mongo_count"] = db.campaigns.count_documents({})
/app/legacy/mongo_archive/legacy-mongo/campaigns_backfill_report.py:39:        report["mongo_error"] = str(exc)
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:75:def _load_from_mongo(mongo_url: str, db_name: str, limit: Optional[int]) -> Iterable[Dict[str, Any]]:
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:77:        from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:79:        raise RuntimeError("pymongo is required for Mongo backfill. Install with: pip install pymongo") from exc
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:81:    client = MongoClient(mongo_url)
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:138:    parser.add_argument("--mongo-url", default=os.environ.get("MONGO_URL"))
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:139:    parser.add_argument("--mongo-db", default=os.environ.get("DB_NAME"))
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:160:        if not args.mongo_url or not args.mongo_db:
/app/legacy/mongo_archive/legacy-mongo/backfill_notifications.py:162:        source_iter = _load_from_mongo(args.mongo_url, args.mongo_db, args.limit)
/app/legacy/mongo_archive/legacy-mongo/seed_mongo_listings.py:10:from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:67:    parser.add_argument('--mongo-url', default=os.environ.get('MONGO_URL'))
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:68:    parser.add_argument('--mongo-db', default=os.environ.get('DB_NAME'))
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:74:    if not args.mongo_url or not args.mongo_db:
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:84:        from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:86:        raise RuntimeError('pymongo is required for moderation migration') from exc
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:88:    mongo_client = MongoClient(args.mongo_url)
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:89:    mongo_db = mongo_client[args.mongo_db]
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:91:    queue_collection = _get_collection(mongo_db, 'moderation_queue')
/app/legacy/mongo_archive/legacy-mongo/migrate_moderation_from_mongo.py:92:    audit_collection = _get_collection(mongo_db, 'moderation_audit')
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:117:def _iter_mongo_listings(mongo_url: str, db_name: str, limit: Optional[int]) -> Iterable[Dict[str, Any]]:
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:119:        from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:121:        raise RuntimeError('pymongo is required for migration script') from exc
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:123:    client = MongoClient(mongo_url)
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:134:    parser.add_argument('--mongo-url', default=os.environ.get('MONGO_URL'))
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:135:    parser.add_argument('--mongo-db', default=os.environ.get('DB_NAME'))
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:142:    if not args.mongo_url or not args.mongo_db:
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:159:    mongo_total = None
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:161:        from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:162:        mongo_client = MongoClient(args.mongo_url)
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:163:        mongo_total = mongo_client[args.mongo_db].listings.count_documents({})
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:165:        mongo_total = None
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:198:    for doc in _iter_mongo_listings(args.mongo_url, args.mongo_db, args.limit):
/app/legacy/mongo_archive/legacy-mongo/migrate_listings_search_from_mongo.py:268:        "mongo_total": mongo_total,
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:19:    from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:21:    raise RuntimeError('pymongo required for moderation parity') from exc
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:23:mongo_client = MongoClient(MONGO_URL) if MONGO_URL and DB_NAME else None
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:24:mongo_db = mongo_client[DB_NAME] if mongo_client and DB_NAME else None
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:28:if mongo_db is not None:
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:29:    collections = mongo_db.list_collection_names()
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:31:        queue_collection = mongo_db.moderation_queue
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:33:        audit_collection = mongo_db.moderation_audit
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:43:queue_mongo_count = queue_collection.count_documents({}) if queue_collection is not None else 0
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:44:audit_mongo_count = audit_collection.count_documents({}) if audit_collection is not None else 0
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:67:    f'Mongo moderation_queue count: {queue_mongo_count}',
/app/legacy/mongo_archive/legacy-mongo/run_moderation_parity.py:69:    f'Mongo moderation_audit count: {audit_mongo_count}',
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:8:from pymongo import MongoClient
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:22:mongo_client = MongoClient(MONGO_URL) if MONGO_URL and DB_NAME else None
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:23:mongo_db = mongo_client[DB_NAME] if mongo_client and DB_NAME else None
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:39:def _mongo_search(query):
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:40:    if mongo_db is None:
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:68:    cursor = mongo_db.listings.find(filters, {"id": 1}).sort(sort_field, sort_dir).limit(20)
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:70:    count = mongo_db.listings.count_documents(filters)
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:132:        mongo_count, mongo_ids = _mongo_search(query)
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:134:        overlap = len(set(mongo_ids) & set(sql_ids))
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:135:        ratio = round((overlap / 20) * 100, 2) if mongo_ids and sql_ids else 0.0
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:138:            "mongo_count": mongo_count,
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:141:            "mongo_ids": mongo_ids,
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:145:    mongo_total = mongo_db.listings.count_documents({}) if mongo_db is not None else 0
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:151:        f"Mongo listing count: {mongo_total}",
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:166:            f"| {row['id']} | {row['mongo_count']} | {row['sql_count']} | {row['top20_overlap_pct']} |"
/app/legacy/mongo_archive/legacy-mongo/run_search_reports.py:179:        raw_lines.append(f"- Mongo IDs (top20): {', '.join(row['mongo_ids']) if row['mongo_ids'] else '[]'}")
```
