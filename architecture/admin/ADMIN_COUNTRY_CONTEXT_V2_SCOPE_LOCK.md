# ADMIN_COUNTRY_CONTEXT_V2_SCOPE_LOCK

## Scope (Kilitle)

### Primary Source of Truth
- **URL query param**: `?country=XX` (XX = ülke code, örn: DE/FR)

### Backend Enforcement (Zorunlu)
- Backend, admin request’lerinde `country` paramını doğrular.
- Country mode’da filtre/guard uygulanır.
- Yetkisiz ülke override denemesi **403** döner.

### Global/Country Mode Switch (UI)
- Header’da kalıcı bir mode toggle:
  - Global mode: URL’de `country` paramı yok.
  - Country mode: URL’de `country=XX` zorunlu.

### LocalStorage
- **Sadece UX hatırlama**:
  - `last_selected_country`
  - URL yoksa (country mode’a geçişte) fallback olarak kullanılır.

## Out of Scope (Bu iterasyon)
- Analytics/event pipeline (search/detail/reveal)
- Finans ve moderasyon modüllerinin tam country-aware raporlaması (endpoint mevcutsa uygulanır).
