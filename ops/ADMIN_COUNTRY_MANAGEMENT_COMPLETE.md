## Admin Country Management (Complete)

### Alanlar
- country_code (PK)
- name
- active_flag
- default_currency
- default_language (opsiyonel)

### Endpoints
- GET `/api/admin/countries`
- GET `/api/admin/countries/{code}`
- POST `/api/admin/countries`
- PATCH `/api/admin/countries/{code}`
- DELETE `/api/admin/countries/{code}` (soft deactivate)

### Audit
- `COUNTRY_CHANGE`
