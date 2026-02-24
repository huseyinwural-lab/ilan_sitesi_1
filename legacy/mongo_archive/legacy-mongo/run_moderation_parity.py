import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import psycopg2

load_dotenv('/app/backend/.env')
load_dotenv('/app/backend/.env.local', override=False)

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL missing for moderation parity')

try:
    from pymongo import MongoClient
except Exception as exc:
    raise RuntimeError('pymongo required for moderation parity') from exc

mongo_client = MongoClient(MONGO_URL) if MONGO_URL and DB_NAME else None
mongo_db = mongo_client[DB_NAME] if mongo_client and DB_NAME else None

queue_collection = None
audit_collection = None
if mongo_db is not None:
    collections = mongo_db.list_collection_names()
    if 'moderation_queue' in collections:
        queue_collection = mongo_db.moderation_queue
    if 'moderation_audit' in collections:
        audit_collection = mongo_db.moderation_audit

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM moderation_queue')
queue_sql_count = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM moderation_actions')
audit_sql_count = cur.fetchone()[0]

queue_mongo_count = queue_collection.count_documents({}) if queue_collection is not None else 0
audit_mongo_count = audit_collection.count_documents({}) if audit_collection is not None else 0

sample_rows = []
if audit_collection is not None:
    cursor = audit_collection.find({}, {}).limit(50)
    for doc in cursor:
        listing_id = str(doc.get('listing_id') or doc.get('listingId') or doc.get('listing') or '')
        action_type = doc.get('action') or doc.get('action_type') or 'unknown'
        cur.execute(
            'SELECT COUNT(*) FROM moderation_actions WHERE listing_id::text=%s AND action_type=%s',
            (listing_id, action_type),
        )
        match_count = cur.fetchone()[0]
        sample_rows.append({
            'listing_id': listing_id,
            'action_type': action_type,
            'match': match_count > 0,
        })

report_lines = [
    '# Moderation Parity Report (Mongo vs Postgres)',
    f'Generated at: {datetime.utcnow().isoformat()}Z',
    '',
    f'Mongo moderation_queue count: {queue_mongo_count}',
    f'SQL moderation_queue count: {queue_sql_count}',
    f'Mongo moderation_audit count: {audit_mongo_count}',
    f'SQL moderation_actions count: {audit_sql_count}',
    '',
    '## Sample Audit Match (50)',
    '| Listing ID | Action | Match |',
    '| --- | --- | --- |',
]

if not sample_rows:
    report_lines.append('| - | - | - |')
    report_lines.append('\n> Not: moderation_audit koleksiyonu bulunamadı veya boş.')
else:
    for row in sample_rows:
        report_lines.append(f"| {row['listing_id']} | {row['action_type']} | {row['match']} |")

Path('/app/memory/MODERATION_PARITY_REPORT.md').write_text('\n'.join(report_lines))
print('MODERATION_PARITY_REPORT.md written')

cur.close()
conn.close()
