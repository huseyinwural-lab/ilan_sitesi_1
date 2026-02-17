# Admin UI Spec — Vehicle Master Data Import Jobs (File‑Based v1)

## 1) Sayfa
- Route: `/admin/master-data/vehicles`
- Amaç: JSON artefact upload → validate/preview → activate → rollback

## 2) UI bileşenleri
### 2.1 Upload
- Input:
  - ZIP (makes.json + models.json)
  - Single JSON bundle
- Upload sonrası server validate sonucu döner.

### 2.2 Validation sonucu / Preview
- Summary kartları:
  - make_count
  - model_count
  - inactive_count
  - alias_count
- Conflict listesi (top N):
  - duplicate_make_keys
  - duplicate_model_keys
  - alias_collisions

### 2.3 Activate
- “Activate” butonu
- Başarılı olursa “Active version” güncellenir.

### 2.4 Rollback
- “Rollback to previous” butonu
- Atomik switch.

### 2.5 Report download
- `validation_report.json` indirilebilir.

## 3) Aktif versiyon bilgisi
- Active version
- Activated at
- Activated by
- Source
- Checksum

## 4) Son 5 job özeti (file-based)
DB job tablosu yok. Kaynak:
- `logs/audit.jsonl` (append-only)

UI’da:
- son 5 satırın özetlenmiş gösterimi.

## 5) Hata raporu
- Son failed import’a ait report linki.
