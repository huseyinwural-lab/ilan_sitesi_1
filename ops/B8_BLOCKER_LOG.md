# B8 Blocker Log

## Blocker Log Entry
- Timestamp (UTC): 2026-02-20T23:36:26.117618+00:00
- PRIMARY_DOMAIN: annonceia.com
- /api/health/db: 520 (DB not ready)
- /api/v1/push/vapid-public-key: 520 (push config not set)
- Boot log: 'push config not set'
- Missing/Unset: DATABASE_URL, DB_SSL_MODE, DB_POOL_MIN/MAX, VAPID_PRIVATE_KEY/VAPID_PUBLIC_KEY/VAPID_SUBJECT (not confirmed)
- READY criteria pending: DB 200 + Push 200 + push config loaded
