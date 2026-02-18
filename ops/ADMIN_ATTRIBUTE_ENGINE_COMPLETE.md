## Admin Attribute Engine (Complete)

### Schema
- id
- category_id
- name
- key
- type (text/number/select/boolean)
- required_flag
- filterable_flag
- options (select için)
- country_code (nullable)
- active_flag
- created_at, updated_at

### Unique
- **(key + category_id + country_code)** kompozit unique

### Endpoints
- **GET /api/admin/attributes** (filters: category_id, country)
- **POST /api/admin/attributes**
- **PATCH /api/admin/attributes/{id}**
- **DELETE /api/admin/attributes/{id}** (soft delete)

### Kurallar
- `select` type için options zorunlu
- Audit-first: `ATTRIBUTE_CHANGE`
- Country-scope zorunlu
