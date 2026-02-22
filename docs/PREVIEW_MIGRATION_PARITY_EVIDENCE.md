# PREVIEW_MIGRATION_PARITY_EVIDENCE

**Tarih:** 2026-02-22 19:12:00 UTC
**Ticket ID:** #1
**SLA:** 24 saat
**Target resolution:** 23 Feb 2026
**Durum:** PASS

## Alembic current
```
alembic current -v
```
Çıktı (özet):
```
Rev: p34_dealer_gdpr_deleted_at (head)
Rev: f3b1c2d8a91b (head)
Rev: c5833a1fffde (head)
Rev: d2f4c9c4c7ab (head)
Rev: aa12b9c8d7e1 (head)
```

## dealer_profiles kolonu doğrulama
```
SELECT column_name FROM information_schema.columns WHERE table_name='dealer_profiles';
```
Sonuç: `gdpr_deleted_at` mevcut.
