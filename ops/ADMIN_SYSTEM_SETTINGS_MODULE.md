## Admin System Settings Module

### KV Schema
- key
- value
- country_code (nullable)
- is_readonly
- description
- updated_at

### Endpoints
- GET `/api/admin/system-settings`
- POST `/api/admin/system-settings`
- PATCH `/api/admin/system-settings/{id}`

### Audit
- `SYSTEM_SETTING_CHANGE`
