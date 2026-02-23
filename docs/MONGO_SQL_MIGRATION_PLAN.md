# MONGO_SQL_MIGRATION_PLAN

**Son güncelleme:** 2026-02-23 23:44:57 UTC

## Tek Seferlik Migrasyon Planı
1) Mongo koleksiyon dump (read-only)
2) SQL hedef tablolarını create_all/migration ile oluştur
3) ID mapping: Mongo string → UUID (yeni UUID üretimi + orijinal id saklama gerekiyorsa metadata JSON)
4) Tarih alanları: ISO string → timezone-aware datetime
5) Nullable kuralları: zorunlu alanlar için default/validation
6) Referential integrity: FK sırası (users → admin_invites → audit_logs)
7) Dedup: email + key + token_hash unique garantisi
8) Verification: count/checksum + örnek kayıt eşlemesi

## Rollback
- SQL snapshot/backup
- Migration log + failed rows raporu