# PREVIEW_MIGRATION_PARITY_EVIDENCE

**Tarih:** 2026-02-22 00:54:38 UTC
**Ticket ID:** #1
**SLA:** 24 saat
**Target resolution:** 23 Feb 2026
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
