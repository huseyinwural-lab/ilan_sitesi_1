# ADMIN_REQUEST_CONTEXT_ENFORCEMENT

## Amaç
Admin request’lerinde Global/Country mode ve country scope’un backend tarafında deterministik uygulanması.

## İşlev
### Mode belirleme
- `?country=XX` varsa => **country mode**
- yoksa => **global mode**

### Country param doğrulama
- `db.countries` üzerinden `code` kontrolü
- Geçersiz => **400**

### Request’e inject
- `request.state.admin_country_ctx`:
  - `mode`: global|country
  - `country`: country code (country mode)

### RBAC
- `country_scope=['*']` => tüm ülkeler
- `country_scope=['DE','FR']` => sadece listede olanlar
- Override => **403**

## Uygulama
- FastAPI dependency (endpoint’lerde çağrılır) veya Starlette middleware.
- MVP’de dependency kullanımı yeterli (hızlı entegrasyon).
