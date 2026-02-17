# VEHICLE MASTER DATA — Public API Contract v1 (File‑Based)

## 1) Genel
- Kaynak: `VEHICLE_MASTER_DATA_DIR/current.json` → active_version → `versions/<version>/makes.json`, `models.json`
- Data global; `country` parametresi v1’de **forward-compat hook**.

## 2) Endpoints
### 2.1 GET /api/v1/vehicle/makes?country=..
Query params:
- `country` (optional) — v1’de sadece cache key / future override hook

Response 200:
```json
{
  "version": "2026-02-17.1",
  "items": [
    {"key": "bmw", "label": "BMW", "popular_rank": 10}
  ]
}
```

### 2.2 GET /api/v1/vehicle/models?make=..&country=..
Query params:
- `make` (required) — make_key
- `country` (optional) — v1’de cache key / future hook

Response 200:
```json
{
  "version": "2026-02-17.1",
  "make": "bmw",
  "items": [
    {"key": "3-serie", "label": "3 Serisi", "year_from": 1975, "year_to": null, "popular_rank": 10}
  ]
}
```

## 3) Cache davranışı
- Server startup’ta active version preload.
- Activate/Rollback cache invalidate eder.

## 4) Error cases
- 400: missing `make`
- 404: make not found
- 500: current manifest okunamaz (prod fail-fast)
