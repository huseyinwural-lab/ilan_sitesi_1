# Notifications E2E Evidence

## Test User
- user@platform.com / User123!

## 1) Listeleme (GET /api/v1/notifications)
- Sonuç: Kullanıcıya ait 2 kayıt döndü.
- Sıralama: `created_at DESC` (Yeni mesaj önce).

## 2) Unread Filter
- `unread_only=true` ile sadece okunmamış kayıt döndü.

## 3) Okundu İşaretleme
- `POST /api/v1/notifications/{id}/read` → `ok: true` ve `read_at` set edildi.

## 4) Permission İzolasyonu
- Başka kullanıcı bildirimi için `POST /read` → **403 Forbidden**.

## 5) Pagination
- `limit=1, page=1` → en yeni kayıt
- `limit=1, page=2` → bir sonraki kayıt

## 6) Index / EXPLAIN
```
EXPLAIN SELECT * FROM notifications
WHERE user_id='02020c1e-afa4-4e6b-9c06-69532f632400' AND read_at IS NULL
ORDER BY created_at DESC LIMIT 10;

Index Scan Backward using ix_notifications_user_created ...
Filter: (read_at IS NULL)
```
