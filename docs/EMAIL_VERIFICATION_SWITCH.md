# EMAIL_VERIFICATION_SWITCH

## Amaç
Email verification akışını **prod‑ready** hale getirmek: debug/mock kodu kaldırmak, gerçek token modeli + expiry enforcement eklemek.

## Mevcut Durum
- `debug_code` response’tan kaldırıldı (mock yok).
- Tokenlar `email_verification_tokens` tablosunda tutuluyor (hash + expires_at + consumed_at).
- TTL: 15 dk (EMAIL_VERIFICATION_TTL_MINUTES=15).

## Hedef (ADR-FINAL-05)
- Debug/mock **tamamen kaldırılacak**.
- Gerçek token modeli + unique index + expiry enforcement.
- TTL: **15 dk** (prod standardı).

## Plan (DB hazır olduğunda)
1) **Yeni tablo:** `email_verification_tokens`
   - `id` (UUID, PK)
   - `user_id` (FK → users.id, index)
   - `token_hash` (String, **unique index**)
   - `expires_at` (DateTime, index)
   - `consumed_at` (DateTime, nullable)
   - `created_at` (DateTime)
   - (Opsiyonel) `ip_address`, `user_agent`

2) **Migration**
   - Unique index: `uq_email_verification_token_hash`.
   - Optional index: `(user_id, created_at)`.

3) **Register / Resend**
   - Yeni token üret → `token_hash` kaydet.
   - Email’e sadece **raw token** gönder.
   - Response’da `debug_code` **dönmeyecek**.

4) **Verify**
   - Token hash ile lookup.
   - `expires_at` kontrolü.
   - `consumed_at` set → user.is_verified = true.
   - Token reuse engeli.

5) **Cleanup**
   - Expired/consumed token cleanup job (günlük).

## Switch Planı
- Yeni tablo + endpoint logic merge edilir.
- `debug_code` field kaldırılır.
- `EMAIL_VERIFICATION_TTL_MINUTES=15` güncellenir.

## Evidence (DB Unblock Sonrası)
- Migration hash + `\d+ email_verification_tokens` çıktısı.
- Register → verify E2E PASS.


## Implementasyon Durumu (Hazırlık)
- `p29_email_verification_tokens` migration hazır (token table + unique index).
- API response’lardan `debug_code` kaldırıldı; mock yok.
- TTL konfigürasyonu 15 dk olarak güncellendi.
- DB gelince migration + E2E doğrulama yapılacak.

