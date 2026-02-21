# PREVIEW_MIGRATION_EVIDENCE

**Tarih:** 2026-02-21
**Durum:** BLOCKED (Preview DB erişimi yok)

## Komutlar (Yapılacak)
```
alembic current
alembic upgrade head
```

## Beklenen Kanıt
- `p34_dealer_gdpr_deleted_at` migration uygulandı
- `dealer_profiles.gdpr_deleted_at` kolonu mevcut

## SQL Kanıt (Yapılacak)
```
\d dealer_profiles
```

> Not: DB erişimi açıldığında gerçek çıktı bu dosyaya eklenecek.
