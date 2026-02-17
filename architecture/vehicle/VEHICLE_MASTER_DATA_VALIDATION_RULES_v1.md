# VEHICLE MASTER DATA — Validation & Dedupe Rules v1 (File‑Based)

## 1) Key format
- `make_key`, `model_key`:
  - lowercase
  - kebab-case
  - ASCII only

## 2) Uniqueness
- `make_key` global unique
- `model_key` make altında unique: `(make_key, model_key)`

## 3) Aliases
- `aliases[]` normalize edilir:
  - trim
  - lowercase compare
- Aynı make/model içinde unique (case-insensitive)

## 4) Alias collision
- Aynı alias, iki farklı make_key veya iki farklı (make_key, model_key) ile çakışıyorsa **reject**.

## 5) Conflict çözümü
- **Merge yok**.
- Conflict → import **reject + report**.

## 6) Required fields
- File meta: version, generated_at, source, checksum
- makes: make_key, display_name, aliases, is_active, sort_order
- models: make_key, model_key, display_name, aliases, is_active (year_from/to opsiyonel)
