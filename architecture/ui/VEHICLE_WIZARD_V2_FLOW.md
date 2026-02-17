# Vehicle Wizard v2 — Flow & UI Blocks (FAZ‑V3 / Aşama 3)

## Step Dizilimi (LOCKED)
1) **Segment**
2) **Make** (API: `/api/v1/vehicle/makes`)
3) **Model** (API: `/api/v1/vehicle/models?make=`)
4) **Year**
5) **Temel Bilgiler**
   - km (mileage_km)
   - fiyat (price_eur)
   - yakıt tipi (fuel_type)  ← elektrikli burada temsil edilir
   - vites (transmission)
   - kondisyon (condition)
6) **Fotoğraflar**
7) **Önizleme + Yayınla**

## UI Bileşenleri
- Stepper + progress bar
- Seçim step’lerinde search + dropdown
- Form step’lerinde inline validation
- Foto step’inde drag-drop + reorder + cover
- Preview step’inde summary + publish CTA

## Country-aware davranış
- Wizard varsayılan country:
  - URL country context veya seçili ülke (CountryContext)
- Master data globaldir; `country` parametresi v1’de cache key olarak geçilir.

## Segment listesi
- otomobil
- arazi-suv-pickup
- motosiklet
- minivan-panelvan
- ticari-arac
- karavan-camper

> Not: Elektrikli segment yok. Elektrikli araçlar `fuel_type = electric` ile seçilir.
