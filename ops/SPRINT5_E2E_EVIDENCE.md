## SPRINT 5 E2E Evidence

### 1) Category create → listing create form’da görünür
```bash
curl -X POST ${REACT_APP_BACKEND_URL}/api/admin/categories \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Cat","slug":"test-cat","country_code":"DE","active_flag":true,"sort_order":10}'

curl ${REACT_APP_BACKEND_URL}/api/categories?module=vehicle&country=DE
```

### 2) Attribute required flag çalışır
```bash
curl -X POST ${REACT_APP_BACKEND_URL}/api/admin/attributes \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"category_id":"<CAT_ID>","name":"VIN","key":"vin","type":"text","required_flag":true}'

curl -X POST ${REACT_APP_BACKEND_URL}/api/v1/listings/vehicle \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Demo","category_key":"<CAT_ID>","country_code":"DE","price_eur":10000}'

curl -X POST ${REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/<LISTING_ID>/submit \
  -H "Authorization: Bearer <USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{}'
```
Beklenen: `validation_error` + missing `vin`.

### 3) Make/Model filtreleri search’te görünür
```bash
curl ${REACT_APP_BACKEND_URL}/api/v1/vehicle/makes?country=DE
curl ${REACT_APP_BACKEND_URL}/api/v1/vehicle/models?make=bmw&country=DE
```

### 4) Country-scope ihlali → 403
```bash
curl -X POST ${REACT_APP_BACKEND_URL}/api/admin/categories \
  -H "Authorization: Bearer <COUNTRY_ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"X","slug":"x","country_code":"FR"}'
```

### 5) Audit log kontrolü
```bash
curl ${REACT_APP_BACKEND_URL}/api/admin/audit-logs?event_type=CATEGORY_CHANGE
```
