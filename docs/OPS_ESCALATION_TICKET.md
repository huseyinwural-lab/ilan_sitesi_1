# OPS_ESCALATION_TICKET

**Başlık:** P0 BLOCKER – DATABASE_URL_PREVIEW Secret Injection Missing
**Ticket ID:** TBD
**SLA:** 48 saat
**Tarih:** 2026-02-22

## İçerik (Ops’a iletilecek)
- DATABASE_URL_PREVIEW runtime env’de **set edilmedi** (printenv boş)
- Firewall/allowlist yok
- /api/health/db → 520 (origin error)

## Beklenen Aksiyonlar
1) Secret manager üzerinden DATABASE_URL_PREVIEW set (sslmode=require, localhost yok)
2) Firewall allowlist: preview backend → Postgres 5432 outbound allow

## Doğrulama
- /api/health/db 200 + db_status=ok
- migration_state: ok / migration_required
