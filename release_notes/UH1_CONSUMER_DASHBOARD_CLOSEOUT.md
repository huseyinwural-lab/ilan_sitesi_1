# UH1 Consumer Dashboard Closeout

**Status:** CLOSED ✅
**Phase:** FAZ-UH1 (Consumer Dashboard V1)

## Scope Delivered
- Aksiyon odaklı consumer dashboard (/account)
- KPI row (yayında, bekleyen, favoriler, mesajlar)
- Primary CTA panel (quota bilgisi + disabled state)
- Son İlanlarım snapshot (status badge + moderation reason tooltip)
- Favoriler / Kayıtlı Aramalar count kartları
- Conditional hesap durumu banner (email/2FA/quota)
- /account/security route + IA v2 menü düzeni

## API Bağımlılıkları
- `/api/v1/listings/my?status=active&limit=1` (yayında ilan)
- `/api/v1/listings/my?status=pending_moderation&limit=1` (bekleyen ilan)
- `/api/v1/favorites/count`
- `/api/v1/messages/unread-count`
- `/api/v1/listings/my?limit=5` (snapshot + moderation_reason)
- `/api/auth/me` (email verified)
- `/api/v1/users/me/2fa/status` (2FA status)

## Open P2 Items
- Saved Search API entegrasyonu (count + “Tümünü gör”)
- Quota API bağlama (limit/remaining)

## Evidence Matrix
| Feature | Test Yöntemi | Kanıt Dosyası | Sonuç |
| --- | --- | --- | --- |
| Dashboard ana görünüm (bloklar) | Playwright screenshot | `/tmp/account-dashboard-uh1.jpg` | PASS |
| /account/security route | Playwright screenshot | `/tmp/account-security-uh1.jpg` | PASS |
| moderation_reason payload | curl | `GET /api/v1/listings/my?limit=1` JSON örneği | PASS |
| /account route 200 | route check | `/account` | PASS |
| /account/security route 200 | route check | `/account/security` | PASS |
