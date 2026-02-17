# IMPLEMENT_FAILED_LOGIN_AUDIT

## Amaç
Başarısız login denemelerini (invalid email/password) `audit_logs` koleksiyonuna kaydetmek.

## Kapsam
- Sadece **başarısız** denemeler loglanır.
- Başarılı login **loglanmaz** (P1 kararı).
- Country alanı **null** bırakılır (P1 kararı).

## Uygulama Notları
- Login endpoint: `POST /api/auth/login`
- Başarısız auth durumunda:
  - HTTP 401 döndür
  - Audit log yaz: `event_type=FAILED_LOGIN`

## Log Alanları (minimum)
- `id`
- `event_type`: `FAILED_LOGIN`
- `action`: `FAILED_LOGIN`
- `email` (request body’den)
- `ip_address`
- `user_agent`
- `created_at` (ISO)

## Kabul Kriteri
- Yanlış şifre ile 3 deneme → `audit_logs` içinde **3** adet `FAILED_LOGIN` kaydı.
