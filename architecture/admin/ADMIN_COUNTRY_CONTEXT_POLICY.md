# ADMIN_COUNTRY_CONTEXT_POLICY

## Karar: Admin Panel’de İki Net Çalışma Modu

### 1) Global Mode
- Amaç: Tüm ülkeleri kapsayan KPI/rapor ve karşılaştırma.
- Kullanım: Yönetici üst seviye operasyon görünümü.

### 2) Country Mode
- Amaç: Seçili ülkeyi etkileyen CRUD ve ülke bazlı metrikler.
- Kullanım: Country selector ile seçilen ülke, **CRUD + metrikleri filtreler**.

## Context Switcher (Header)
- Header’da tek bir “Context Switcher” bulunur.
- **Country** seçimi context switcher’dadır.
- **Language** seçimi ayrı bir kontrol olarak kalır (Country + Language aynı kontrol DEĞİL).

## Uygulama Notları
- Country mode açıkken:
  - Ülkeye bağlı CRUD sayfaları (Ülkeler hariç) default olarak seçili ülkeye göre filtrelenir.
  - Global metrikler “total” olarak ayrıca gösterilebilir.
- Global mode açıkken:
  - Ülke filtresi yoktur veya “All countries” şeklinde davranır.

## Risk / Trade-off
- Mode ayrımı UI’da bir miktar ekstra kontrol getirir.
- Buna karşılık admin deneyimi deterministik hale gelir.
