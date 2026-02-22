# HEALTH_MIGRATION_GATE_SPEC

## Amaç
DB bağlı olsa bile Alembic head değilse servis “ready” sayılmasın.

## API
`GET /api/health/db`

## Yeni Alanlar
- `migration_state`: `ok | migration_required | unknown`
- `migration_head`: Alembic head revizyonu (varsa)
- `migration_current`: DB'deki revizyon (alembic_version)

## Davranış
- **Preview/Prod**: `migration_required` → HTTP **503**
- **Local/Dev**: `migration_required` → HTTP **200**, `status=degraded`
- `unknown`: 200 + `status=degraded`

## Cache
- Migration kontrolü **60 saniye** cache’lenir.

## Notlar
- Health endpointi yoğun çağrıldığından DB yükü azaltılır.
