# SPRINT1_PREVIEW_API_EVIDENCE

**Tarih:** 2026-02-21
**Durum:** BLOCKED (Preview DB erişimi yok)

## Consumer
```
GET /api/v1/users/me/profile
GET /api/v1/users/me/data-export
DELETE /api/v1/users/me/account
```

## Dealer
```
GET /api/v1/users/me/dealer-profile
```

## Beklenen
- Profile 200
- Export JSON
- Delete soft delete (gdpr_deleted_at + 30 gün)

> Not: Preview DB erişimi açıldığında gerçek curl çıktıları eklenecek.
