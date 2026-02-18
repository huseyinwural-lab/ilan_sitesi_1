## Sprint 4 E2E Evidence

### Zorunlu Testler
1) **Country CRUD + audit**
- POST `/api/admin/countries` → `TR`
- PATCH `/api/admin/countries/TR` → name update
- Audit: `COUNTRY_CHANGE`

2) **System settings CRUD + audit**
- POST `/api/admin/system-settings` (global + TR override)
- Audit: `SYSTEM_SETTING_CHANGE`

3) **Dashboard KPI’lar gerçek veri dönüyor**
- GET `/api/admin/dashboard/summary?country=DE` → KPI set
- GET `/api/admin/dashboard/country-compare`

4) **Country-scope ihlali → 403**
- Country admin ile `/api/admin/dashboard/summary?country=FR` → 403

### Komutlar (özet)
```bash
curl -X POST $REACT_APP_BACKEND_URL/api/admin/countries \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"country_code":"TR","name":"Turkey","default_currency":"TRY","default_language":"tr"}'

curl -X POST $REACT_APP_BACKEND_URL/api/admin/system-settings \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"key":"billing.vat_rate_default","value":19}'

curl -X GET "$REACT_APP_BACKEND_URL/api/admin/dashboard/summary?country=DE" \
  -H "Authorization: Bearer <TOKEN>"
```
