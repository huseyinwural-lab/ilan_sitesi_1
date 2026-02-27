# ADMIN_INVITE_PREVIEW_SPEC

**Tarih:** 2026-02-24 11:21:40 UTC
**Ortam URL:** https://feature-complete-36.preview.emergentagent.com

## Beklenen Davranış
- Token yoksa: **422** (expected validation)
- Token geçersiz/used/expired: **404** (Invite not found)
- Token geçerli: **200** (email/role/expires_at döner)

## Test Komutları
- `curl {BASE}/api/admin/invite/preview`
- `curl {BASE}/api/admin/invite/preview?token=INVALID_TOKEN_123`
- `curl {BASE}/api/admin/invite/preview?token=INVITE_PREVIEW_TEST_TOKEN`

## Sonuçlar
- Token yok: 422
- Geçersiz token: 404
- Geçerli token: 200 (email=invitee@platform.com, role=support)

## Not
- Preview ortamında doğrulama için örnek token: `INVITE_PREVIEW_TEST_TOKEN`
