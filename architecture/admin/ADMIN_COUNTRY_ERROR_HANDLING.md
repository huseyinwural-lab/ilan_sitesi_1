# ADMIN_COUNTRY_ERROR_HANDLING

## Senaryolar

### 1) Geçersiz country
- Ör: `?country=ZZ`
- Backend: **400** (Invalid country parameter)
- UI: global moda dön veya geçerli son seçime redirect.

### 2) Yetkisiz country
- Ör: country_scope=['DE'] iken `?country=FR`
- Backend: **403** (Country scope forbidden)
- UI: mevcut allowed ülkeye redirect veya açıklayıcı hata.

### 3) Mode mismatch
- Country mode beklenen sayfada param yoksa:
  - UI: last_selected ile redirect

## Not
- Backend, enforcement dependency ile bu hataları standardize eder.
