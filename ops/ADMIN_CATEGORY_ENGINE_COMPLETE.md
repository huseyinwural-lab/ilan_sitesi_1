## Admin Category Engine (Complete)

### Schema
- id
- parent_id (nullable)
- name
- slug
- country_code (nullable = global)
- active_flag
- sort_order
- module = vehicle
- created_at, updated_at

### Unique
- **(slug + country_code)** kompozit unique
- country_code null = global

### Endpoints
- **GET /api/admin/categories**
  - Query: `country` (optional)
  - Flat response + parent_id
- **POST /api/admin/categories**
- **PATCH /api/admin/categories/{id}**
- **DELETE /api/admin/categories/{id}** (soft delete)

### Kurallar
- Audit-first: `CATEGORY_CHANGE`
- Country-scope zorunlu
- slug formatı doğrulanır (kebab-case)
