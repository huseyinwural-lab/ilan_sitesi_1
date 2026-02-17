# FAZ‑V3 / Aşama 2 (REV‑B) — Acceptance Gate

Bu doküman, file-based JSON master data akışının “bitti” sayılması için gerekli kriterleri ve kanıt formatını tanımlar.

## Gate Kriterleri (LOCKED)
1) JSON bundle upload/validate/activate/rollback çalışır
2) Public makes/models API current versiyondan servis eder
3) Validation strict, merge yok (conflict → reject + report)
4) Audit log yazılır (append-only JSONL)
5) Deploy sürecinde data directory yönetimi tanımlı (`VEHICLE_MASTER_DATA_DIR=/data/vehicle_master`)

## Kanıtlar (bu sprint sonunda doldurulacak)
- Backend test çıktıları:
  - validate OK/FAIL örnekleri
  - activate + rollback OK
  - public API makes/models OK
- Audit log sample satırları
- Admin UI smoke (upload → preview → activate → rollback)

Durum: **PASSED**

## Kanıtlar (özet)
- Admin UI flow (Playwright): upload → validate → activate → rollback ✅
- Backend API:
  - GET /api/v1/vehicle/makes ✅
  - GET /api/v1/vehicle/models ✅
  - Admin validate/activate/rollback ✅
- Audit log örneği: `/data/vehicle_master/logs/audit.jsonl` içinde IMPORT_ACTIVATE + ROLLBACK satırları ✅

