## P1 — Master Data CSV Import/Export Tasarımı

### Kapsam
- Categories, Attributes, Vehicle Makes, Vehicle Models
- Country-aware (country_code nullable → global)

### Export
- Endpoint (admin):
  - `GET /api/admin/master-data/export?entity=category|attribute|vehicle_make|vehicle_model&country=DE`
- CSV kolonları:
  - **Category:** id, parent_id, name, slug, country_code, active_flag, sort_order
  - **Attribute:** id, category_id, name, key, type, required_flag, filterable_flag, options, country_code, active_flag
  - **VehicleMake:** id, name, slug, country_code, active_flag
  - **VehicleModel:** id, make_id, name, slug, active_flag

### Import
- Endpoint (admin):
  - `POST /api/admin/master-data/import?entity=...&mode=upsert`
- Validasyonlar:
  - Category slug uniqueness (slug+country_code)
  - Attribute key uniqueness (key+category_id+country_code)
  - Model slug uniqueness (slug+make_id)
  - Soft delete destekli
- Audit:
  - CATEGORY_CHANGE / ATTRIBUTE_CHANGE / VEHICLE_MASTER_DATA_CHANGE

### Idempotency
- `mode=upsert`: slug/key üzerinden update
- `mode=insert`: duplicate slug/key → 409
