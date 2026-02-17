# VEHICLE MASTER DATA — File Audit & Sync Log v1 (JSONL)

## 1) Log formatı
- Append-only JSONL dosyası:
  - `logs/audit.jsonl`
  - (opsiyonel) `logs/sync.jsonl`

Her satır bir JSON objesidir:
```json
{
  "ts": "2026-02-17T12:35:00Z",
  "event": "IMPORT_VALIDATE" | "IMPORT_ACTIVATE" | "ROLLBACK",
  "user_id": "<admin_user_id>",
  "source": "manual-upload",
  "version": "2026-02-17.1",
  "checksum": "<sha256>",
  "status": "OK" | "FAILED",
  "diff_summary": {
    "make_count": 120,
    "model_count": 980,
    "inactive_count": 12
  },
  "error_sample": [
    {"code": "DUPLICATE_MAKE_KEY", "message": "Duplicate make_key: bmw"}
  ]
}
```

## 2) Rotation / retention
- v1 default:
  - Dosya boyutu > 20MB → rotate (ör: audit.1.jsonl)
  - Son 5 rotate saklanır

## 3) Sync log
- Provider entegrasyonu v2’de gelirse `sync.jsonl` kullanılacak.
- v1’de sync log opsiyoneldir.
