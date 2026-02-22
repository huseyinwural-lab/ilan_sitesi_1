# PREVIEW_UNBLOCK_TRACKER

**Tarih:** 2026-02-22
**Durum:** Preview DB blocker aktif

## Local (PASS)
- Health migration gate kodu hazır
- Register honeypot (company_website) UI+backend hazır
- GDPR export notification (in-app, warning) hazır
- v1 profile/dealer/2FA/soft delete/export endpointleri hazır

## Preview (BLOCKED/PENDING)
- [ ] DATABASE_URL_PREVIEW secret injection (sslmode=require, localhost yok)
- [ ] Firewall allowlist (preview → Postgres 5432)
- [ ] /api/health/db 200 + db_status=ok
- [ ] Migration gate doğrulaması (A: 503 migration_required, B: 200 ok)
- [ ] alembic current/upgrade head + p34 kolonu kanıtı
- [ ] Sprint‑1 E2E curl kanıtları (profile/dealer/export/delete)
- [ ] Honeypot 400 + register_honeypot_hit audit
- [ ] Export notification + audit doğrulama

## Ticket
- Ops Ticket: TBD
- SLA: 48 saat
