# Vehicle Wizard v2 — Scope Lock (FAZ‑V3 / Aşama 3)

## 1) Kapsam (LOCKED)
Wizard v2, Vasıta ilanı üretimi için adım adım akışı sağlar:

### Segmentler (LOCKED)
**Elektrikli segment değildir.**
Elektrikli = `fuel_type` attribute ile temsil edilir.

Segment listesi:
- `otomobil`
- `arazi-suv-pickup`
- `motosiklet`
- `minivan-panelvan`
- `ticari-arac`
- `karavan-camper`

### Make/Model kaynağı (LOCKED)
- Make/Model seçimleri yalnızca **file-based master data public API** üzerinden gelir:
  - GET `/api/v1/vehicle/makes?country=..`
  - GET `/api/v1/vehicle/models?make=..&country=..`

### Zorunlu/opsiyonel
- `year` zorunlu
- `trim` opsiyonel **placeholder** (v2’de UI gösterilebilir ama master data bağlanmaz)

### Teknik alanlar
- Bu aşamada **gerçek spec auto-fill yok** (v3.4)
- Teknik alanlar UI’da manuel girilir (opsiyonel alanlar contract’a göre)

### Foto kalite
- Minimum foto: **3** (hard-block)
- Minimum çözünürlük: policy dokümanında tanımlanır (hard-block)

## 2) Hariç (Explicitly Out of Scope)
- VIN, hasar kaydı, servis geçmişi (v4)
- Provider bazlı gerçek spec auto-fill (v3.4)
- Trim master data (v3.x)
- Fraud/Trust layer hard-block (v3.5+)

## 3) Kabul kriteri özeti
- Wizard akışı tamam (segment→make→model→year→basic→photos→preview→publish)
- Make/model enforce (invalid seçim publish’te reject)
- Foto kalite standardı publish’i hard-block eder
