# LEGACY_PUBLISH_DEPRECATION_PLAN

Tarih: 2026-02-27

## Kapsam
Legacy endpoint:
- `POST /api/admin/ui/configs/{config_type}/publish/{config_id}`

Yeni endpoint:
- `POST /api/admin/ui/configs/{config_type}/publish`

## Son 30 Gün Kullanım Analizi

Analiz endpointi:
- `GET /api/admin/ui/configs/{config_type}/legacy-usage?days=30`

Çıktı:
- toplam çağrı sayısı
- actor bazlı breakdown

## Deprecation Aşamaları

### Aşama 1 (Tamamlandı)
- Endpoint deprecated işaretli
- Audit: `ui_config_publish_legacy_call`

### Aşama 2 (Tamamlandı)
- Legacy endpoint çağrısı artık **410 Gone**
- Response:
  - `code = LEGACY_ENDPOINT_REMOVED`
  - deprecation header’ları (`Deprecation`, `Sunset`, `Link`)

### Aşama 3 (P2 Cleanup)
- OpenAPI’den legacy path çıkarımı
- Client SDK referans temizliği
- Route kodunun fiziksel kaldırılması

## Kontrat Temizliği

Hedef:
- Tek publish kontratı (new endpoint)
- Legacy usage sıfıra indiğinde route kaldırımı

## Regression Checklist

- Legacy endpoint çağrısı -> `410`
- Yeni endpoint publish -> PASS
- Snapshot integrity -> PASS
