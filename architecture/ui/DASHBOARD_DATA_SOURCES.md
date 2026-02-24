# Dashboard Data Sources

## Primary Sources
- **Yayında İlan Sayısı:** `/api/v1/listings/my?status=active&limit=1` → `pagination.total`
- **Bekleyen İlan Sayısı:** `/api/v1/listings/my?status=pending_moderation&limit=1` → `pagination.total`
- **Favoriler:** `/api/v1/favorites/count` → `count`
- **Mesajlar (30g):** `/api/v1/messages/unread-count` → `count`
- **Son İlanlarım:** `/api/v1/listings/my?limit=5`
- **Account status:** `/api/auth/me` (email verified), `/api/v1/users/me/2fa/status` (2FA)

## Fallback (Deterministic)
- API yok/başarısız: `0` + “Veri hazırlanıyor” etiketi.
- Saved searches ve quota için API yoksa aynı fallback uygulanır.
