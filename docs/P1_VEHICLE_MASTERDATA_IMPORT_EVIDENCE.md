# P1 Vehicle Master Data Import Evidence

Date: 2026-02-25

## UI
- Admin ekranı: `/app/screenshots/admin-vehicle-master-import.png`

## API — Upload Job (dry-run)
- Job create (upload):
  - `POST /api/admin/vehicle-master-import/jobs/upload` → 200
  - Örnek job id: `b0b65456-4efa-4e56-aabd-eca6a6f774f1`
- Job status:
  - `GET /api/admin/vehicle-master-import/jobs/{job_id}` → 200
  - `status: succeeded`, `processed_records: 1`, `summary.new: 1`

## API — Invalid JSON
- `POST /api/admin/vehicle-master-import/jobs/upload` (JSON array değil) → 400
- Mesaj: `JSON must be an array of records`

## Observability
- Audit log: `VEHICLE_IMPORT_STARTED`, `VEHICLE_IMPORT_COMPLETED`, `VEHICLE_IMPORT_FAILED` (kod seviyesi)
- Summary metrikleri: new/updated/skipped + distinct make/model/trim + validation errors + süre
