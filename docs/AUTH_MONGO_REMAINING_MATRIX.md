# AUTH_MONGO_REMAINING_MATRIX

## Durum Özeti
- Critical Path auth akışları (register/login/verify/resend) **SQL-only**.
- `server.py` içinde **AUTH_PROVIDER == "mongo"** fallback’ları kaldırıldı.

## Kalan Mongo Bağımlılıkları (Critical Path Dışı)
- `/users/me/export` (GDPR metadata export) → Mongo tabanlı
- Push subscription endpoints (`/v1/push/*`) → Mongo tabanlı

## Karar
- Bu kalanlar **Critical Path dışı** olduğundan FINAL‑01 kapsamında engel değildir.
- Mongo Zero fazında ayrıca ele alınacak.
