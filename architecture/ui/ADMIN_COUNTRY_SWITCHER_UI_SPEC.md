# ADMIN_COUNTRY_SWITCHER_UI_SPEC

## Bileşen
Header’da kalıcı bir “Admin Context Switcher”.

## UI Elemanları
1) Mode toggle
- Global / Country

2) Country dropdown
- Sadece Country mode’da aktif
- Ülkeler: DE/CH/FR/AT (flags ile)

## Davranış
- Global mode => URL’den `country` silinir.
- Country mode => URL’de `?country=XX` zorunlu.
  - XX yoksa last_selected_country veya default ile set edilir.

## LocalStorage
- `last_selected_country` sadece UX hatırlama.

## Test IDs
- admin-mode-toggle
- admin-mode-switch
- country-selector
- country-select-{CODE}
