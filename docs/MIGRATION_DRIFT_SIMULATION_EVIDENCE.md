# MIGRATION_DRIFT_SIMULATION_EVIDENCE

**Tarih:** 2026-02-22 00:54:38 UTC
**Durum:** BLOCKED (Local Postgres yok)

## Denenen Komut
```
APP_ENV=preview DB_SSL_MODE=require DATABASE_URL=postgresql://localhost:5432/admin_panel alembic current
```
Çıktı (özet):
```
psycopg2.OperationalError: connection to server at "localhost" (127.0.0.1), port 5432 failed
```

## Beklenen Akış (DB hazır olduğunda)
1. `alembic current`
2. `alembic downgrade -1`
3. `/api/health/db` → 503 + migration_required
4. `alembic upgrade head`
5. `/api/health/db` → 200 + migration_state=ok
