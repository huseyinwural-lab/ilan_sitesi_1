# Vehicle Publish Guard Policy v1 (Hard‑Block)

Publish guard, `/submit` çağrısında çalışır ve tüm kurallar hard‑block’tur.

## 1) Master data enforcement
- make_key master’da yoksa → 422
- model_key make altında yoksa → 422
- inactive make/model → 422

## 2) Segment required fields
- Segment matrisi (Stage‑3 dokümanı) authoritative’dir.
- Eksik alan → 422

## 3) Media policy enforcement
- min 3 foto → 422
- her foto min 800x600 → 422

## 4) Country
- `country` zorunlu (DE/CH/FR/AT)

## 5) Error format
- `validation_errors[]` normalize edilir:
  - field
  - code
  - message

Not: mileage/year sanity soft‑warning bu aşamada yok; publish hard‑block.
