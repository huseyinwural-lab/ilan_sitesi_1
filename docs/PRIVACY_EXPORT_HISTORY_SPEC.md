# PRIVACY_EXPORT_HISTORY_SPEC

## Amaç
GDPR veri export taleplerinin izlenmesi ve yeniden indirme akışının sağlanması.

## Kapsam
- Export talepleri **gdpr_exports** tablosunda loglanır.
- Kullanıcı “Export Geçmişi” ekranından geçmiş talepleri görür.
- Başarılı exportlar için “Yeniden indir” butonu sunulur.

## Veri Modeli (SQL)
**gdpr_exports**
- id (UUID, PK)
- user_id (UUID, FK → users.id, index)
- created_at (timestamp, default now)
- file_path (string, nullable)
- status (enum: pending, ready, failed)

## Backend Akışı
1. `/api/v1/users/me/data-export` çağrısı geldiğinde:
   - gdpr_exports kaydı **pending** olarak açılır.
   - Export oluşturulur.
   - Başarılı ise status=ready, file_path set edilir.
   - Hata varsa status=failed.
2. `/api/v1/users/me/exports` (GET)
   - Kullanıcının export geçmişini döner.
3. `/api/v1/users/me/exports/{export_id}/download` (GET)
   - Sadece owner erişebilir.

## UI (Privacy Center)
- “Export Geçmişi” listesi
  - created_at
  - status badge
  - download button (status=ready)

## Audit/Compliance
- Her export talebi için audit log (event: gdpr_export_requested).
- Export geçmişi 12 ay saklama önerisi.

## Notlar
- V1’de JSON-only export devam eder.
- Dosya saklama için S3 veya lokal storage stratejisi netleştirilmeli.
