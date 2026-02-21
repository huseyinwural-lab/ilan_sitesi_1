# Decommission: Campaigns (Mongo)

## Durum
- Campaigns read/write **tamamen SQL** (`campaigns` tablosu).
- Mongo collection kullanımı kaldırıldı.

## Arama Kanıtı
- Anahtar: `db.campaigns`
- Sonuç: **0**

## Notlar
- Audit log için SQL `audit_logs` kullanılıyor.
