## Admin Vehicle Master Data (Complete)

### Make Schema
- id
- name
- slug
- country_code
- active_flag
- created_at, updated_at

### Model Schema
- id
- make_id
- name
- slug
- active_flag
- created_at, updated_at

### Unique
- Make: **(slug + country_code)**
- Model: **(slug + make_id)**

### Endpoints
- **GET /api/admin/vehicle-makes** (country optional)
- **POST /api/admin/vehicle-makes**
- **PATCH /api/admin/vehicle-makes/{id}**
- **DELETE /api/admin/vehicle-makes/{id}**
- **GET /api/admin/vehicle-models** (make_id optional)
- **POST /api/admin/vehicle-models**
- **PATCH /api/admin/vehicle-models/{id}**
- **DELETE /api/admin/vehicle-models/{id}**

### Kurallar
- Audit-first: `VEHICLE_MASTER_DATA_CHANGE`
- Country-scope make üzerinde zorunlu
