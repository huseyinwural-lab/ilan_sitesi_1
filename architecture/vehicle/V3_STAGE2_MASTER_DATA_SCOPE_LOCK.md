# FAZ‑V3 / Aşama 2 (REV‑B) — Master Data Scope Lock (File‑Based JSON, DB/Mongo YOK)

## 1) Kapsam (Locked)
Bu sprintte “Vehicle Master Data” **runtime’da DB kullanmadan**, sadece dosya tabanlı JSON artefact’lerinden servis edilecektir.

### Minimum kapsam (v1)
- **make** (brand)
- **model** (make altında)
- (opsiyonel) model bazlı **year_from / year_to**

### Bu sprintte YOK
- Provider entegrasyonu (CarQuery vb.)
- Trim / variant / engine / drivetrain gibi derin otomotiv master data
- DB tabanlı job tablosu veya DB üzerinden master data yazımı

## 2) Data Kaynağı (Locked)
- Kaynak: `VEHICLE_MASTER_DATA_DIR` altındaki **aktif versiyon manifest’inin işaret ettiği** `makes.json` ve `models.json`.
- Repo içinde tutulmaz (ops policy ayrı dokümanda).
- Aktivasyon/rollback “manifest pointer switch” ile atomik.

## 3) Admin İthalat Akışı (Locked)
Admin yalnızca artefact yükler:
- Upload → Validate → Preview → Activate
- Rollback

Çakışma/konfliktte **merge yok**:
- “Reject + report” (güvenli MVP)

## 4) Country-aware politika (Locked)
- `make_key` / `model_key` **global**.
- `country` parametresi v1’de **forward-compat hook**:
  - cache key
  - ileride country-override / localization / alias genişletmeleri

## 5) Public API (Locked)
- GET `/api/v1/vehicle/makes?country=..`
- GET `/api/v1/vehicle/models?make=..&country=..`

Yanıtlar file-based current versiyondan servis edilir.

## 6) Güvenlik / Prod davranışı (Locked)
- App startup’ta current manifest okunamazsa **fail-fast** (prod güvenliği).
- Cache invalidate yalnızca **activate/rollback** ile.
