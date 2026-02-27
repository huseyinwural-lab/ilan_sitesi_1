# LEGACY_PUBLISH_DEPRECATION_PLAN

Tarih: 2026-02-27

## Kapsam
Legacy endpoint:
- `POST /api/admin/ui/configs/{config_type}/publish/{config_id}`

Yeni endpoint:
- `POST /api/admin/ui/configs/{config_type}/publish`

## Son 30 Gün Kullanım Analizi

Not:
- Legacy usage analiz endpointi (`/legacy-usage`) P2 fiziksel temizlik kapsamında kaldırıldı.
- Geçmiş kullanım analizi için sadece mevcut audit kayıtları (DB) sorgulanır.

## Deprecation Aşamaları

### Aşama 1 (Tamamlandı)
- Endpoint deprecated işaretli
- Audit: `ui_config_publish_legacy_call`

### Aşama 2 (Tamamlandı)
- Legacy endpoint çağrısı `410 Gone` ile yönlendirme yapıyordu

### Aşama 3 (Tamamlandı - P2 Cleanup)
- OpenAPI’den legacy path çıkarıldı
- Client SDK referans temizliği tamamlandı
- Route kodu fiziksel olarak kaldırıldı

## Kontrat Temizliği

Hedef:
- Tek publish kontratı (new endpoint)
- Legacy route/usage endpointlerinin fiziksel kaldırımı

## Regression Checklist

- Legacy endpoint çağrısı -> `404` (route yok)
- Yeni endpoint publish -> PASS
- Snapshot integrity -> PASS
