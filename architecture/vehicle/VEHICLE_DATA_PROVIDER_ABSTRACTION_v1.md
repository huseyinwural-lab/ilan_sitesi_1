# VEHICLE DATA PROVIDER ABSTRACTION v1 (DB‑independent)

Bu doküman, provider entegrasyonu bu sprintte yapılmasa da, provider output’unun **file-based JSON bundle** formatına dönüştürülmesi için arayüzü kilitler.

## 1) Provider çıktısı → JSON bundle
Provider’dan gelen data doğrudan runtime’a bağlanmaz. Provider çıktısı bir build/ops aşamasında JSON artefact’e dönüştürülür:

- Input: provider API / export
- Normalize: key üretimi, alias mapping
- Validate + dedupe
- Output: `makes.json` + `models.json` veya single bundle

## 2) Provider interface (concept)
- `list_makes()` → raw makes
- `list_models(make)` → raw models

## 3) Normalization
- Key üretimi:
  - `make_key = normalize(display_name)`
  - `model_key = normalize(display_name)`
- Aliases:
  - farklı yazımlar aliases’e eklenebilir

## 4) Dedupe stratejisi
- v1 rule: conflict → reject (merge yok)
- Provider dönüşüm pipeline’ı conflict raporu üretmelidir.

## 5) Lisans / redistribution metadata
Artefact meta alanları:
- `source`
- (opsiyonel) `license`, `redistribution_allowed`, `terms_url`

> Not: Bu alanlar v1’de zorunlu değildir; ancak provider seçildiğinde kilitlenebilir.
