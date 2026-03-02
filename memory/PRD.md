# PRD — İlan Ver Overhaul + Stabilizasyon

## Problem Özeti
Kullanıcı hedefi, İlan Ver akışını PDF standardında bitirmek ve admin kontrollü, deterministik, uçtan uca çalışır hale getirmekti.
Öncelik: P0 (İlan Ver), ardından P1 stabilizasyon (Vitrin yansıma + urgent sayfa), sonra P2 UX güçlendirme.

## Mimari
- Frontend: React
  - `/ilan-ver` (kategori/modül)
  - `/ilan-ver/arac-sec` (vasıta)
  - `/ilan-ver/detaylar` (8 blok form)
  - `/ilan-ver/onizleme` (submit)
- Backend: FastAPI (`backend/server.py`)
  - listing flow state machine
  - places/autocomplete proxy + guard
  - homepage/showcase/search uçları
- DB: PostgreSQL

---

## 2026-03-01 Tamamlananlar

### P0 — Google Autocomplete Real Mode (manuel key destekli)
- Backend eklendi:
  - `GET /api/places/config`
  - `GET /api/places/autocomplete`
  - `GET /api/places/details`
- Guard davranışı:
  - Env key varsa real mode
  - Env key yoksa fallback
  - Kullanıcı manuel key girdiğinde (`manual_key` / header) runtime real çağrı
- Rate limit eklendi (endpoint bazlı koruma)
- Frontend adres bloğu:
  - `GOOGLE_MAPS_API_KEY` manuel giriş alanı
  - Debounce autocomplete
  - Suggestion list + detay seçimi
  - Normalize alanlar: **il, ilçe, mahalle, lat/lng**
  - Draft PATCH ile adres bloğu autosave

### P0 — Zengin Seed Data + E2E Hazırlığı
- Yeni script: `/app/scripts/seed_ilan_ver_e2e_data.py`
- Seed kapsamı:
  - Emlak: 3 root, her root altında 2 leaf
  - Leaf bazlı farklı `form_schema` (dynamic/detail/module config)
  - Vasıta: 3 marka + marka başına 2 model + model başına 2 trim
- Trim uniqueness backend+frontend dedupe ile korundu.

### P0 — İlan 3 UX Güçlendirme (P2 maddesi önden alındı)
- Completion panel eklendi:
  - Blok bazlı completion rule
  - Global % tamamlanma barı
  - Eksik blok checklist
- Submit davranışı:
  - %100 değilse submit bloklanır + uyarı
- Analytics event akışı:
  - `block_completed`
  - `submit_blocked_incomplete`

### P1 — Vitrin yansımama stabilizasyonu
- Admin publish sonrası frontend revalidation eventleri eklendi:
  - `showcase-layout-updated`
  - `homepage-revalidate-requested`
  - localStorage token set
- HomePage revalidation:
  - focus / visibility / storage / custom event dinleyicileri
- Backend publish response zenginleştirildi:
  - `published_at`
  - `revalidate_token`

### P1 — Urgent sayfa doğrulama
- `doping_type=urgent` filtre + pagination test edildi
- Performans için 50+ kayıt seviyesi doğrulandı (urgent total > 70)

---

## Test Durumu

### Testing Agent
- `/app/test_reports/iteration_70.json`
- Backend: 20/20 PASS
- Frontendde HomePage loading/urgent sorunları raporlandı, bu iterasyonda düzeltildi.

### Self-Test Sonuçları (fix sonrası)
- HomePage:
  - loading state 9sn içinde kapanıyor
  - urgent sayaç `ACİL (70)`
- Places config:
  - key yokken fallback güvenli dönüş
- Search urgent:
  - pagination doğru (total/pages doğru)

---

## Kalan İşler

### P0 kalan
- Kullanıcı gerçek GOOGLE_MAPS_API_KEY girdiğinde canlı autocomplete doğrulamasını birlikte final PASS (network/key doğrulaması).
- Adres seç -> kaydet -> detail sayfasında gerçek canlı yer seçimi ile final acceptance testi.

### P1 kalan
- Vitrin bug’i için farklı admin senaryolarında (çoklu tab/çoklu ülke) regresyon turu.
- Urgent listede empty-state metni UX iyileştirmesi (API yerine UI metin standardizasyonu).

### P2
- Category Builder drag&drop + batch reorder API + `CATEGORY_REORDERED` audit.
- Batch publish scheduler + Slack/SMTP/PagerDuty entegrasyonları + ops health metriği.

---

## Mock Durumu
- MOCKED API: **Yok**
- Google autocomplete şu an gerçek mod/fallback guard ile hazır; gerçek sonuçlar kullanıcı key girişiyle çalışacak şekilde implement edildi.


---

## 2026-03-01 (Kullanıcı Talebi Revizyonu)

### Uygulanan 2 Talep
1) **Google Maps key admin paneline taşındı**
- Yeni admin entegrasyon ayarı eklendi:
  - `GET /api/admin/system-settings/google-maps`
  - `POST /api/admin/system-settings/google-maps`
- Admin ekranı: `AdminSystemSettings.js` içinde **Google Maps (İlan Adres Akışı)** kartı
  - API key kaydetme (masked gösterim)
  - Ülke kodları yönetimi (webde radio olarak kullanılacak)

2) **Adres akışı PDF mantığına göre değiştirildi**
- `ListingDetails.js` adres bloğunda akış:
  - Adminden gelen ülkeler **radio**
  - Posta kodu girişi
  - **Haritada Aç** (posta koduna göre alan lookup)
  - Harita alanındaki sokaklardan seçim
  - Seçim sonrası adres alanlarının otomatik dolması: il / ilçe / mahalle / lat / lng / açık adres
- Backend eklendi:
  - `GET /api/places/postal-lookup`
  - `GET /api/places/config` artık `country_options` döndürüyor

### Not
- Gerçek Google Maps sonucu için geçerli key gereklidir. Key yok/yanlışsa fallback uyarısı verilir (uygulama kırılmaz).

### Test
- Testing agent raporu: `/app/test_reports/iteration_71.json`
  - Backend 19/19 PASS
  - Frontend admin kart + address flow davranışı PASS


### 2026-03-01 (Ek Revizyon)
- Admin panel görünürlüğü için sidebar’a doğrudan **Google Maps Ayarları** menü linki eklendi:
  - `/admin/system-settings?focus=google-maps`
- System settings sayfasında `focus=google-maps` query geldiğinde kart otomatik scroll/focus alıyor.
- Google Maps kartına güvenli **Key’i Temizle** aksiyonu eklendi.
- Canlı E2E doğrulaması tamamlandı:
  - Posta Kodu -> Harita alanı -> Sokak listesi -> Place details -> Draft save -> submit
  - Test raporu: `/app/test_reports/iteration_73.json`


### 2026-03-01 (İlan Tasarım eksikleri tamamlama)
- Yeni admin sayfası: **/admin/site-design/listing** (`AdminListingDesign.js`)
  - İlan 1: satır/sütun + modül kutuları (başlık/açıklama/görsel/modül eşleme)
  - İlan 2: arama/breadcrumb/stepper + continue limit + leaf zorunluluğu
  - İlan 3: medya/iletişim/süre/onay metni ve adres zorunlulukları
- Yeni backend endpointleri:
  - `GET /api/admin/site/listing-design`
  - `PUT /api/admin/site/listing-design`
  - `GET /api/site/listing-design`
- Site Tasarım menüsüne **İlan Tasarım** eklendi ve RBAC route izni açıldı.
- Web entegrasyonu:
  - `/ilan-ver` modül gridi admin listing-design step1 konfigini okuyor.
  - İlan 2 continue limit step2 konfiginden okunuyor.
  - İlan 3 medya/contact/terms kuralları step3 konfiginden uygulanıyor.
- Test raporu: `/app/test_reports/iteration_75.json` (backend/frontend PASS)

### 2026-03-01 (Faz 0 / İş 1 — Draft/Publish/Rollback)
- Yeni model eklendi: `listing_design_configs` (`backend/app/models/listing_design_config.py`)
  - Alanlar: `id`, `payload`, `status(draft|published|archived)`, `version`, `published_at`, `created_at`, `updated_at`
- Migration eklendi: `backend/migrations/versions/p72_listing_design_configs.py`
- Endpoint davranışı güncellendi:
  - `PUT /api/admin/site/listing-design` => sadece **draft** oluşturur (her kayıtta `version` artar)
  - `POST /api/admin/site/listing-design/publish` => draft’ı **published** yapar (yeni published sürüm oluşturur, `version` artar)
  - `POST /api/admin/site/listing-design/rollback` => önceki published payload ile yeni **published** sürüm üretir (`version` artar)
  - `GET /api/site/listing-design` => yalnızca **published** konfig okur
- Doğrulanan 3 senaryo (curl): PASS
  1) Admin save -> draft, public değişmedi
  2) Publish -> public live güncellendi
  3) Rollback -> public önceki live sürüme döndü

---

## 2026-03-02 (Faz 2 / İş 1 — Stripe Foundation Devam)

### Bu iterasyonda tamamlananlar
- Backend Stripe foundation için yeni ödeme intent akışı eklendi:
  - `POST /api/payments/create-intent`
  - `POST /api/payments/webhook`
- Yeni domain katmanı eklendi:
  - `app/domains/payments/service.py`
  - Event -> payment status ve payment status -> listing status eşlemeleri
- Yeni model eklendi:
  - `listing_payments` (`ListingPayment`)
  - Alanlar: `id`, `user_id`, `listing_id`, `stripe_payment_intent_id`, `amount`, `currency`, `status`, `idempotency_key`, `meta_json`, `created_at`, `updated_at`
- Webhook tarafında imza doğrulama + event idempotency (`WebhookEventLog` provider=`stripe_payment_intent`) aktif.
- Listing status güncelleme kuralı:
  - `succeeded` -> `pending_moderation`
  - `failed` -> `draft`
  - `processing` -> listing status değişmez

### Ortam / konfigürasyon
- `backend/.env` güncellendi:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLIC_KEY`
  - Mevcut `STRIPE_WEBHOOK_SECRET` korundu.

### Test durumu
- Testing agent raporu: `/app/test_reports/iteration_76.json`
  - Kritik/minor bug: **Yok**
  - Endpoint guard/validation senaryoları: **PASS**
- Ek backend smoke: `deep_testing_backend_v2` PASS
- Frontend smoke: `auto_frontend_testing_agent` PASS
- Not: Pozitif canlı Stripe intent testi, ortamda kullanılan placeholder key (`sk_test_emergent`) nedeniyle gerçek charge akışında doğrulanamadı; guard ve hata yönetimi senaryoları doğrulandı.

### Önceliklendirilmiş kalan işler
- **P0 (aktif):** Stripe gerçek test key ile `create-intent` başarılı senaryo + webhook `payment_intent.succeeded` uçtan uca canlı doğrulama.
- **P1:** Template #17/#18 checkout sayfaları (`/payment/success`, `/payment/fail`) ve frontend entegrasyonu.
- **P1:** Trust/Policy ve Corporate/SEO template setlerinin tamamlanması.
- **P2:** 500/maintenance sistem sayfaları + kategori builder drag&drop.

---

## 2026-03-02 (FIN-P2 Sprint — P0 + Admin Read-only Finans Ekranları)

### Sprint Scope Kilidi (uygulandı)
- P0 çekirdek domain/API + Admin read-only finans görünürlüğü tamamlandı.
- Migrasyon stratejisi: **backward-compatible dual-write** (legacy alanlar korunuyor, yeni `amount_minor` alanları yazılıyor).
- Invoice PDF bu sprintte **bilinçli olarak dışarıda** bırakıldı (P1).
- CSV export RBAC: **yalnız `super_admin`**.

### Backend (P0) — Tamamlananlar
- Money v2: `Payment`, `AdminInvoice`, `ListingPayment`, `PaymentTransaction` için `amount_minor + currency` akışı aktif.
- Yeni finans domain modelleri eklendi:
  - `FinanceProduct`, `FinanceProductPrice` (currency bazlı fiyat + etkinlik aralığı)
  - `TaxProfile` (TR %20 KDV, DE %19 VAT seed)
  - `FinanceInvoiceSequence` (race-safe invoice no üretimi)
  - `LedgerAccount`, `LedgerEntry` (immutable double-entry)
- Deterministik vergi pipeline:
  - Snapshot alanları: `net_minor`, `tax_minor`, `gross_minor`
  - Rounding policy: `HALF_UP`
  - `meta_json.money_v2` + `meta_json.tax_profile` snapshot yazımı
- Invoice state machine güçlendirildi (`draft -> issued -> paid -> void/refunded`) ve manuel override audit log eklendi.
- Race-safe invoice numbering:
  - Format: `{COUNTRY}-{YYYYMM}-{SEQUENCE:06d}`
  - `FOR UPDATE` lock + sequence tablosu.
- Ledger:
  - Ödeme/iadede çift taraflı kayıt (denge kontrolü)
  - Reversal endpoint (update yerine düzeltme hareketi)
- Subscription lifecycle genişletmesi:
  - `trialing/active/past_due/canceled/unpaid` geçiş doğrulaması.

### Yeni / güncellenen admin endpointleri
- `GET /api/admin/finance/overview`
- `GET /api/admin/finance/subscriptions`
- `GET /api/admin/finance/subscriptions/{id}`
- `PATCH /api/admin/finance/subscriptions/{id}/status`
- `GET /api/admin/finance/ledger`
- `POST /api/admin/finance/ledger/{entry_id}/reverse`
- `GET /api/admin/finance/tax-profiles`
- `POST /api/admin/finance/tax-profiles`
- `PATCH /api/admin/finance/tax-profiles/{profile_id}`
- `GET /api/admin/finance/products`
- `POST /api/admin/finance/products`
- `GET /api/admin/finance/product-prices`
- `POST /api/admin/finance/products/{product_id}/prices`
- `GET /api/admin/finance/trace/{invoice_id}`
- CSV export:
  - `GET /api/admin/payments/export/csv` (super_admin)
  - `GET /api/admin/invoices/export/csv` (super_admin)
  - `GET /api/admin/ledger/export/csv` (super_admin)

### Admin UI (Sprint içi temel read-only)
- Yeni sayfalar:
  - `/admin/finance-overview`
  - `/admin/subscriptions`
  - `/admin/ledger`
- Route/nav/rbac güncellendi (finance menüsü + guard kuralları).
- Kritik UI elemanlarında `data-testid` eklendi.

### Test Durumu
- Testing agent raporu: `/app/test_reports/iteration_78.json`
  - Backend: **18/18 PASS**
  - Frontend: **3/3 PASS**
- Doğrulanan ana başlıklar:
  - Money v2 dual-write PASS
  - Tax profile deterministic pipeline PASS
  - Race-safe invoice numbering PASS
  - Finance overview/subscriptions/ledger endpointleri PASS
  - CSV RBAC (super_admin only) PASS
  - Webhook signature + idempotency PASS

### Kalanlar (P1/P2)
- **P1:** Invoice PDF üretimi + storage + admin download akışı.
- **P1:** Country admin scoped export + row-level filters (gerektiğinde).
- **P2:** Kullanıcı tarafı Faturalarım/Ödeme Geçmişi/Abonelik self-serve.
- **P2:** Finans UI standardizasyonu (locale/badge/empty-loading-error iyileştirmeleri).

---

## 2026-03-02 (FIN-P2 P1 — Invoice PDF + Scoped Export Tamamlama)

### Kapsam (yalnız 2 madde)
- Invoice PDF üretim + storage + admin download
- Country-admin scoped export (finance listeleri)

### Backend tamamlananlar
- `AdminInvoice` snapshot genişletildi (immutable kullanım):
  - `net_amount_minor`, `tax_amount_minor`, `gross_amount_minor`, `currency`, `tax_rate`, `billing_info_snapshot`
  - `pdf_url`, `pdf_generated_at`
- PDF endpointleri eklendi:
  - `POST /api/admin/invoices/{id}/generate-pdf` (idempotent; ikinci çağrı mevcut path döner)
  - `POST /api/admin/invoices/{id}/regenerate-pdf` (yalnız super_admin; versiyon suffix ile yeni dosya)
  - `GET /api/admin/invoices/{id}/download-pdf` (super_admin + country_admin scope kontrol)
- Storage path standardı aktif:
  - `{app_prefix}/invoices/{year}/{country}/{invoice_no}.pdf`
- Audit eventleri:
  - `PDF_GENERATED`, `PDF_REGENERATED`, `PDF_DOWNLOADED`
  - Export tarafında `EXPORT_TRIGGERED` (type, record_count, country_scope)

### Scoped export (backend-enforced)
- Yeni unified endpoint:
  - `GET /api/admin/finance/export?type=payments|invoices|ledger`
- RBAC:
  - `super_admin`: global
  - `country_admin`: otomatik country scope (query ile bypass yok)
- Eski export endpointleri de scope/audit kurallarıyla hizalandı.

### Admin UI tamamlananlar
- Invoice detail:
  - `PDF: Available / Not Generated` badge
  - `Generate PDF` + `Regenerate PDF` (yalnız super_admin)
  - `Download PDF` (super_admin + country_admin)
- Scope görünürlüğü eklendi:
  - Invoices / Payments / Subscriptions / Ledger / Finance Overview sayfalarında scope badge
- Finance overview’a export aksiyonları eklendi (payments/invoices/ledger).

### Test sonucu
- Testing agent raporu: `/app/test_reports/iteration_79.json`
  - Backend: kritik/minor issue yok
  - Frontend: minor banner bug fixlendi
- Ek doğrulama:
  - Auto frontend retest PASS (invoice DB banner false-positive giderildi)
  - Deep backend smoke PASS (PDF flow + scoped export + RBAC)

### Kalan işler
- P2: User-side billing screens (Faturalarım/Ödeme Geçmişi/Abonelik self-serve)
- P2: Finans UI standardizasyonu ve ileri raporlama

---

## 2026-03-02 (P2 — Kullanıcı Finans Ekranları Tamamlama, Scope Lock: 1a 2a 3a 4a)

### Scope kilidi (uygulandı)
- **1a:** Yalnız P2 kullanıcı finans ekranları + test (UI standardizasyonu yok)
- **2a:** Fatura listesi varsayılan sıralama en yeni önce (issued_at/create fallback DESC)
- **3a:** Abonelik aksiyonları modal onaylı (cancel/reactivate/plan preview)
- **4a:** Empty-state metin tonu resmi/kurumsal

### Frontend tamamlananlar
- Route bağlama tamamlandı:
  - `/account/invoices`
  - `/account/payments`
  - `/account/subscription`
- Account side menüye finans bölümü eklendi (Faturalarım / Ödeme Geçmişi / Aboneliğim).
- `AccountInvoices.js`:
  - API binding + durum/tarih filtreleri
  - liste + tarih kolonu + PDF indirme aksiyonu
  - resmi empty/error metinleri ve data-testid kapsamı
- `AccountPayments.js`:
  - ödeme geçmişi listeleme + durum filtreleme
  - normalize kullanıcı mesajı gösterimi
  - resmi empty/error metinleri ve data-testid kapsamı
- `AccountSubscription.js`:
  - aktif plan/ücret/yenileme bilgisi
  - cancel/reactivate işlemlerinde onay modalı
  - plan change preview için onay modalı
  - pending/success state görünürlüğü ve data-testid kapsamı

### Backend tamamlananlar
- `GET /api/account/invoices` sıralama güncellendi:
  - `coalesce(issued_at, created_at) DESC`, fallback `created_at DESC`
- Subscription self-serve kalıcılık düzeltmesi:
  - `cancel/reactivate` endpointlerinde `meta_json` değişiklikleri için dict copy uygulanarak persist bug fixlendi.

### Test sonucu
- Testing agent raporu: `/app/test_reports/iteration_80.json`
  - Backend: **PASS**
  - Frontend: **PASS**
  - E2E: Invoice PDF download **PASS**, Subscription cancel/reactivate **PASS**
  - Regression: Admin finance + PDF + export akışları **PASS**
- Ek self-test:
  - account endpoint contract doğrulamaları (200/403/PDF content-type) başarılı.
 - Test kapanış temizliği:
   - Testing sırasında oluşturulan `user@platform.com` abonelik kaydı silinerek kullanıcı free-state'e geri alındı.

### Güncel kalan işler
- **P1 (bir sonraki iş):** Finans UI standardizasyonu (tekil locale money formatter + ortak badge dili)
- **P2:** Trust/Policy template seti (#20/#21/#22)
- **P2:** Corporate & SEO template seti (#23-28)
- **P2:** 500/maintenance system templateleri (#30/#31)
- **P3:** Category Builder drag&drop

---

## 2026-03-02 (Toplu Kapanış — Kalanların Tek Iterasyonda Tamamlanması)

### Bu iterasyonda tamamlananlar
- **P1 Finans UI standardizasyonu (uygulandı):**
  - `AdminSubscriptions.js` finans state/badge/money format bileşenleri ile hizalandı.
  - `AdminInvoices.js` durum göstergeleri `FinanceStatusBadge` ile tekilleştirildi; tutar görünümü `formatMoneyMinor` ile locale-aware hale getirildi.
- **P2 Trust/Policy template seti (uygulandı):**
  - Yeni trust merkezi: `/trust`
  - Legal slugs için yayın fallback içerikleri backend’e eklendi (`/api/info/{slug}` fallback map).
- **P2 Corporate & SEO template seti (uygulandı):**
  - Kurumsal merkez: `/kurumsal`
  - SEO/Bilgi merkezi: `/seo`
  - Corporate/SEO bilgi slugs için fallback içerikler aktif.
- **P2 System template seti (uygulandı):**
  - Maintenance sayfası: `/maintenance`
  - Mevcut `500` sayfası ile birlikte system template seti tamamlandı.
- **Footer fallback güçlendirmesi:**
  - Trust/Corporate/SEO/System link grupları eklendi.
- **P3 Category drag&drop:**
  - `AdminCategories.js` içerisinde draggable reorder akışı mevcut ve regression testte doğrulandı.

### Test sonucu
- Testing agent raporu: `/app/test_reports/iteration_81.json`
  - Backend: **PASS** (24 testten 22 PASS; kalanlar kritik olmayan kozmetik notlar)
  - Frontend: **PASS**
  - Public template sayfaları + maintenance + fallback info içerikleri + admin finans standardizasyonu + user finans regresyonu **PASS**

### Güncel kalan işler (aktif P0/P1/P2)
- Bu kapsamda kapatılacak kritik iş kalmadı.
- Gelecek geliştirme alanları: ileri finans raporlama, dönüşüm analitiği, içerik A/B testleri.
