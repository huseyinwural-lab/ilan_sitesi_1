# PREVIEW_MIGRATION_PARITY_EVIDENCE

**Tarih:** 2026-02-22
**Ticket ID:** TBD
**SLA:** 48 saat
**Durum:** BLOCKED (Preview DB erişimi yok)

## Komutlar (Yapılacak)
```
alembic current
alembic upgrade head
```

## Beklenen
- Head revizyonu = DB revizyonu
- p34_dealer_gdpr_deleted_at kolon mevcut

## SQL Kanıt (Yapılacak)
```
\d dealer_profiles
```
