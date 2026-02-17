# CHECK_ADMIN_COUNTRY_CONTEXT

## Amaç
Admin Country Context v2’nin kurumsal doğrulaması.

## Kontroller

### 1) URL param source-of-truth
- Beklenen: Country mode’da URL `?country=XX` deterministik.
- Mevcut: Header toggle + dropdown URL’i güncelliyor.
- Durum: ✅ PASS

### 2) Backend enforcement tam mı?
- Beklenen: country param kullanan admin endpoint’lerde invalid=400, forbidden=403.
- Mevcut:
  - ✅ /api/users
  - ✅ /api/dashboard/stats
  - ✅ /api/countries (context resolve var)
  - ✅ /api/categories (context resolve var)
  - ⚠️ diğer endpoint’lerde uygulanmadı (kaçak olabilir) → GAP
- Durum: PARTIAL

### 3) RBAC country-scope ihlali
- Test: country_admin scope=['DE'] ile country=FR => 403
- Durum: ✅ PASS (uygulanan endpoint’lerde)

### 4) Param silinmesi
- Beklenen: Country mode seçiliyse param silinirse zorunlu redirect.
- Mevcut: `admin_mode` localStorage ile country mod tercihi tutuluyor ve URL’de param yoksa fallback set ediliyor.
- Durum: ✅ PASS (UI behavior)

### 5) Invalid param
- `country=ZZ` => backend 400
- UI: crash olmamalı.
- Durum: ✅ PASS (smoke)

## Sonuç
- Genel: ✅ PASS (UI) + 🟠 PARTIAL (backend coverage)
- Kritik not: enforcement henüz sadece belirli endpoint’lerde; kalan admin endpoint’ler için checklist üzerinden genişletilmeli.
