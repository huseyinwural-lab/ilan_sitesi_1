# VEHICLE MASTER DATA — Import Pipeline v1 (REV‑B)

## 1) Amaç
Admin üzerinden master data artefact’inin sisteme yüklenmesi, doğrulanması, preview edilmesi ve atomik olarak aktive edilmesi.

## 2) Accepted Inputs (LOCKED)
v1’de iki format birlikte desteklenir:

1) **ZIP bundle**
- İçerik:
  - `makes.json`
  - `models.json`

2) **Single JSON bundle**
- Tek dosya JSON:
```json
{
  "makes": { ...makes.json format... },
  "models": { ...models.json format... }
}
```

## 3) Pipeline adımları
### 3.1 Upload
- Admin artefact yükler (ZIP veya bundle).

### 3.2 Validate
- Schema validation (required fields, types)
- Dedupe + uniqueness kuralları
- Checksum doğrulama

### 3.3 Preview
- Sayımlar:
  - make_count
  - model_count
  - inactive_count
  - alias_count
- Conflict summary:
  - duplicate_make_keys
  - duplicate_model_keys
  - alias_collisions

### 3.4 Activate
- Artefact `versions/<version_id>/` altına yazılır.
- `manifest.json` yazılır.
- `current.json` atomik switch.

### 3.5 Rollback
- Önceki versiyona `current.json` atomik switch.

## 4) Validation Report formatı (JSON)
- `validation_report.json` version klasöründe saklanır.
- İndirme için admin UI’dan sunulur.

Örnek:
```json
{
  "ok": false,
  "version": "2026-02-17.1",
  "errors": [
    {"code": "DUPLICATE_MAKE_KEY", "message": "Duplicate make_key: bmw"}
  ],
  "summary": {
    "make_count": 120,
    "model_count": 980,
    "inactive_count": 12
  }
}
```
