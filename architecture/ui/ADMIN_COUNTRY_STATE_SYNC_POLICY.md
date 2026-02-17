# ADMIN_COUNTRY_STATE_SYNC_POLICY

## Kural: URL Primary Source of Truth
- Admin country scope sadece URL üzerinden belirlenir.
- Context/State sadece UI senkronizasyonu içindir.

## Sync
- URL `country` değiştiğinde:
  - CountryContext `selectedCountry` sync edilir (flags/UX).
- Mode toggle:
  - Global => param sil
  - Country => param set

## LocalStorage
- Son seçim: `last_selected_country`
- URL’de param yoksa (country mode’a geçiş): fallback olarak kullanılır.
