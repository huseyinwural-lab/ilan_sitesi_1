# VEHICLE MASTER DATA — File Schema Standard v1 (REV‑B)

Bu doküman, Vehicle Master Data’nın **file-based JSON artefact** formatını standardize eder.

## 1) Dosyalar (minimum)
- `makes.json`
- `models.json`

## 2) Ortak üst seviye meta (ZORUNLU)
Her dosya aşağıdaki alanları içermelidir:
- `version` (string) — Örn: `"2026-02-17.1"`
- `generated_at` (ISO8601 string, UTC) — Örn: `"2026-02-17T12:00:00Z"`
- `source` (string) — Örn: `"manual-upload"` / `"provider:xyz"`
- `checksum` (string) — SHA256 hex (artefact bütünlüğü)

### Örnek:
```json
{
  "version": "2026-02-17.1",
  "generated_at": "2026-02-17T12:00:00Z",
  "source": "manual-upload",
  "checksum": "<sha256>",
  "items": []
}
```

## 3) makes.json schema
`items[]` elemanları:
- `make_key` (string, required)
- `display_name` (string, required)
- `aliases` (string[], required, boş olabilir)
- `is_active` (bool, required)
- `sort_order` (int, required)

Örnek item:
```json
{
  "make_key": "bmw",
  "display_name": "BMW",
  "aliases": ["Bayerische Motoren Werke"],
  "is_active": true,
  "sort_order": 10
}
```

## 4) models.json schema
`items[]` elemanları:
- `make_key` (string, required)
- `model_key` (string, required)
- `display_name` (string, required)
- `aliases` (string[], required, boş olabilir)
- `year_from` (int, optional)
- `year_to` (int, optional)
- `is_active` (bool, required)

Örnek item:
```json
{
  "make_key": "bmw",
  "model_key": "3-serie",
  "display_name": "3 Serisi",
  "aliases": ["3 series", "3er"],
  "year_from": 1975,
  "year_to": null,
  "is_active": true
}
```

## 5) Checksum
- `checksum`, dosyanın `items` + meta içeriği baz alınarak SHA256 ile üretilir.
- v1’de algoritma: canonical JSON (sorted keys) + UTF‑8.

> Not: Checksum hesaplama yöntemi pipeline dokümanında kesinleştirilir.
