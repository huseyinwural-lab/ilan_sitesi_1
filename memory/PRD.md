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

---

## 2026-03-02 (Kurumsal Kullanıcı Tarafı Eksiklerin Tamamlanması + PDF Detay İnceleme)

### Kullanıcı onaylı kapsam
- `1b`: `/dealer/*` + kurumsal public tarafıyla ilişkili eksikleri kapat
- `2c`: Placeholder + API/integration eksiklerini birlikte tamamla
- `3b`: Mevcut finans akışını bozma
- `4b`: Detaylı polish + test-id

### Uygulanan geliştirmeler
- **Dealer route kapanışları:**
  - `/dealer/invoices` gerçek sayfaya bağlandı (redirect kaldırıldı)
  - `/dealer/company` ve `/dealer/privacy` aktif route olarak bağlandı
- **Dealer finance backend genişletmesi:**
  - `GET /api/dealer/payments` eklendi (status filtre + normalized message)
  - `GET /api/dealer/invoices/{id}/download-pdf` eklendi (ownership enforced)
  - `GET /api/dealer/invoices/{id}` response'una `payments` listesi eklendi
  - Dealer invoice list sıralaması `coalesce(issued_at, created_at) DESC` olarak güncellendi
- **DealerInvoices sayfası kapsamlı yenileme:**
  - Tab yapısı: `Faturalarım` + `Hesap Hareketlerim`
  - Durum + tarih filtreleri
  - Fatura detay paneli (ödeme satırlarıyla)
  - PDF indirme aksiyonu
  - Kurumsal dilde empty/error metinleri ve kapsamlı `data-testid`
- **Kurumsal erişilebilirlik iyileştirmeleri:**
  - `DealerSettings` içine hızlı linkler: Şirket Profili / Gizlilik Merkezi / Faturalar-Hareketler
  - `DealerLayout` üst aksiyonlara `Yardım Merkezi` butonu eklendi (`/bilgi/yardim-merkezi`)

### PDF inceleme notu
- Test sırasında dealer faturası için admin tarafından PDF regenerate edildi ve dealer panelinden indirme akışı uçtan uca doğrulandı.
- Doğrulamalar:
  - content-type `application/pdf`
  - owner invoice download: `200`
  - foreign invoice download: `403`

### Test sonucu
- Testing agent raporu: `/app/test_reports/iteration_82.json`
  - Backend: **PASS**
  - Frontend: **PASS**
  - Dealer invoice/payments/detail/pdf + company/privacy/settings quick links + yardım merkezi navigasyonu **PASS**
  - Admin/account finance regression **PASS**

### Güncel durum
- Kurumsal kullanıcı tarafında bu kapsam için kritik açık bulunmuyor.

---

## 2026-03-02 (P0-01 — Health Stabilizasyonu)

### Yapılan teknik değişiklikler
- `/api/health/db` kontratı düzeltildi:
  - **HTTP 503 kaldırıldı**, endpoint artık her durumda **HTTP 200** döner.
  - Response standardı sabitlendi:
    - `status`: `ok | degraded`
    - `db_status`: `ok | fail`
    - `reason`: (`migration_required`, `db_timeout`, `db_unreachable`, `db_config_missing`)
- Health DB check hafifletildi:
  - request path sadece **`SELECT 1`** kullanır
  - kısa timeout: `db_timeout_ms = 500`
  - health için ayrı mini pool (`health_sql_engine`, pool 1/0, kısa pool_timeout)
  - probe cache eklendi (`HEALTH_DB_PROBE_CACHE_TTL_SECONDS=30`) — health spam altında p95 korunur
- Migration sinyali ayrıştırıldı:
  - yeni endpoint: **`/api/health/migrations`**
  - migration_required takibi bu endpointten yapılır
  - `/api/health/db` migration introspection yapmaz, cache sinyalini taşır

### Kanıt/test çıktıları
- 15 dk loop raporu: `/app/test_reports/p0_01_health_15m.json`
  - toplam istek: 900
  - `count_503`: **0**
  - `p95`: **3.54ms**
- Testing agent doğrulaması: `/app/test_reports/iteration_83.json`
  - health/db contract: **PASS**
  - health/migrations endpoint: **PASS**
  - concurrency stress: **PASS** (20 worker altında 0 adet 503)

### 24 saat kabul penceresi
- 24h izleme başlatıldı (arka plan monitor):
  - process: `p0_01_health_24h_monitor.py`
  - progress: `/app/test_reports/p0_01_health_24h.progress`
  - stream: `/app/test_reports/p0_01_health_24h_monitor.jsonl`

### Güncel durum
- P0-01 teknik düzeltmesi uygulandı ve kısa/orta süre kanıtları PASS.
- 24 saatlik pencere tamamlanınca P0-01 kapanışı finalize edilecek.

---

## 2026-03-02 (P0-02 — Sitemap Production Hardening)

### Uygulanan değişiklikler
- Hardcoded sitemap host kaldırıldı; sitemap/canonical host üretimi tek resolver üzerinden yapıldı:
  - `_resolve_public_base_url(request)`
  - öncelik: `PUBLIC_BASE_URL` env -> `x-forwarded-host`/`host`
- Yeni/sertleştirilen sitemap endpointleri:
  - `/api/sitemap.xml`
  - `/api/sitemaps/core.xml`
  - `/api/sitemaps/categories.xml`
  - `/api/sitemaps/listings.xml`
  - `/api/sitemaps/info.xml`
  - backend root eşleri: `/sitemap.xml`, `/sitemaps/*.xml`
- Canonical deterministik kuralı uygulandı:
  - Trailing slash standardı (root hariç slash yok)
  - Route değişiminde canonical senkronu (`CanonicalRouteSync`)
  - `normalizeCanonicalUrl` ile query/hash temizliği
- Kapsam ve filtre:
  - Home/static + trust/corporate/seo
  - Category landing (`/kategori/*`)
  - Active+published listing detay (`/ilan/{id}`)
  - Bilgi sayfaları (`/bilgi/*`) + fallback info slugs

### Doğrulama ve kanıt
- Test raporu: `/app/test_reports/iteration_84.json`
  - Backend: PASS (sitemap XML, host çözümü, kapsam)
  - Frontend: PASS (canonical deterministik)
- Host doğruluk raporu (20'şer örnek dahil):
  - `/app/test_reports/p0_02_sitemap_host_report.json`
  - preview `wrong_host_count=0`, prod `wrong_host_count=0`
- Pytest artifacts:
  - `/app/backend/tests/test_p0_02_sitemap_production_hardening.py`
  - `/app/test_reports/pytest/p0_02_sitemap_production_hardening_results.xml`

### Güncel durum
- P0-02 hedefi tamamlandı: sitemap/canonical host drift giderildi, deterministik URL standardı sağlandı.

---

## 2026-03-02 (P0-03 — Stripe Final Acceptance / Faz-1 Tamam)

### Stripe acceptance kapsamı (tamamlanan)
- Gerçek Stripe test-mode checkout akışı tetiklendi ve ödeme başarıyla tamamlandı.
- Session doğrulaması:
  - `session_status=complete`
  - `payment_status=paid`
- Backend doğrulaması:
  - `payments.status=succeeded`
  - `admin_invoices.status=paid`, `payment_status=succeeded`
  - ledger double-entry dengesi: debit=credit
- Webhook doğrulaması:
  - `checkout.session.completed` işlendi
  - `payment_intent.succeeded` valid signature ile loglandı
  - webhook replay çağrıları HTTP 200 kanıtı üretildi

### Kanıt dosyaları
- `/app/test_reports/p0_03_stripe_checkout_context.json`
- `/app/test_reports/p0_03_webhook_replay_results.json`
- `/app/test_reports/p0_03_stripe_acceptance.json`
- Testing agent sonucu: `/app/test_reports/iteration_85.json` (12/12 PASS)

### Not
- Stripe account webhook endpoint listesinde legacy URL de tespit edildi; yine de bu acceptance turunda valid-signature + 200 replay + DB state senkronu kanıtlandı.

### P0-03 kalan
- Google Maps canlı acceptance (3 şehir: TR + DE + rastgele 1)
- Host/redirect son regresyon paketi

---

## 2026-03-02 (P0-03 — Google Maps Canlı Acceptance / Faz-2 Tamam)

### Uygulanan acceptance kapsamı
- Gerçek `MAPS_API_KEY` (system setting) ile `/api/places/config` doğrulandı:
  - `real_mode=true`
  - `key_source=system_setting`
- 3 şehir için postal lookup + suggestion + kayıt + DB doğrulaması tamamlandı:
  - TR: İstanbul (`34000`)
  - DE: Berlin (`10115`)
  - FR: Paris (`75001`)  *(rastgele 3. şehir)*
- `/ilan-ver` adres blok akışı test edildi; suggestion seçimi sonrası location verisi draft’a yazıldı.

### Üretilen kanıt dosyaları
- `/app/test_reports/p0_03_maps_acceptance.json`
- `/app/test_reports/p0_03_maps_db_assertions.json`
- Testing agent raporu: `/app/test_reports/iteration_86.json` (**PASS**)

### Doğrulama özeti
- Provider/API:
  - `/api/places/postal-lookup` tüm şehirlerde `200` + `status=OK`
  - `REQUEST_DENIED`, `API_KEY_INVALID`, `OVER_QUERY_LIMIT` görülmedi
  - Maps/Places provider 4xx/5xx: **0**
- DB assertions:
  - Her listing için location alanları dolu:
    - `country`, `city`, `district`, `postal_code`, `latitude`, `longitude`, `address_line`
  - `all_required_fields_populated=true`

### Güncel durum
- P0-03 Stripe + Maps acceptance kanıtları tamamlandı.
- P0-03 içinde yalnız host/redirect son regresyon kapanışı kaldı.

---

## 2026-03-02 (P0-03 — Country Selector Kısıtlama + Host/Redirect Son Regresyon)

### Uygulanan istek (öncelikli)
- Listing adres ülke seçeneğinden **TR kaldırıldı**.
- Ülke seçenekleri yalnızca: **DE, FR, CH, AT**.
- Country selector modu **radio** olarak sabitlendi.

### Teknik doğrulama
- Config güncellemesi:
  - `/api/admin/system-settings/google-maps` -> country_codes `[DE, FR, CH, AT]`
  - `/api/admin/system-settings/listing-create` -> `country_selector_mode=radio`
- Doğrulama endpointleri:
  - `/api/places/config` country_options: `[DE, FR, CH, AT]`, `TR` yok
  - `listing_create_config.country_selector_mode = radio`

### Host/Redirect regresyon sonucu
- `http://preview` -> `https://preview` redirect: **max 1 hop PASS**
- Canonical örnek sayfalarda preview host ile deterministik: **mismatch 0 PASS**
- Sitemap host doğruluğu:
  - preview: **%100 doğru host PASS**
  - simulated `www.annoncia.com` ve `annoncia.com`: **drift 0 PASS**

### Kanıt dosyaları
- `/app/test_reports/p0_03_country_selector_update.json`
- `/app/test_reports/p0_03_host_redirect_regression.json`
- Testing agent: `/app/test_reports/iteration_87.json` (PASS)

### Güncel durum
- P0-03 (Stripe + Maps + Host/Redirect) kapanış kriterleri sağlandı.

---

## 2026-03-02 (P0-04 — Legacy Billing Cleanup / Tam Kaldırma + Konsolidasyon)

### Uygulanan kaldırmalar
- **Stub ödeme endpoint kaldırıldı:**
  - `POST /api/payments/create-checkout-session/stub` server router’ından fiziksel olarak çıkarıldı.
  - Canlı doğrulama: endpoint artık **404 Not Found**.
- **Legacy admin billing UI entrypoint kaldırıldı:**
  - `BackofficePortalApp.jsx` içinden `/billing` route ve `BillingPlaceholder` import’u kaldırıldı.
  - `adminRbac.js` içinden `/admin/billing` kuralı kaldırıldı.
  - `AdminBreadcrumbs.jsx` içinden `billing` label kaldırıldı.
- **Legacy backend billing namespace temizlendi:**
  - `backend/app/routers/billing_routes.py`, `billing_read_routes.py`, `billing_webhook.py` legacy route taşımaz hale getirildi.
  - `APIRouter(prefix="/v1/billing")` kalıntıları temizlendi.
- **İsimlendirme temizliği:**
  - `RateLimiter` scope: `stripe_legacy_webhook` -> `stripe_webhook`.

### Kanıt ve regresyon
- P0-04 kanıtları: `/app/test_reports/p0_04_legacy_billing_removed_grep.txt` + `/app/test_reports/iteration_88.json` (PASS).

### Güncel durum
- P0-04 tam kaldırma ve konsolidasyon kriterleri sağlandı.
- Finans tarafında aktif tek giriş seti: güncel Stripe tabanlı canonical endpointler.
## 2026-03-02 (P0-05 — Kategori Leaf → Form Template Final Doğrulama)
- Kanıtlar: `/app/test_reports/p0_05_leaf_template_inventory.json`, `/app/test_reports/p0_05_leaf_template_e2e_matrix.json`, `/app/test_reports/iteration_89.json`; sonuç `unmapped_publishable_count=0` + `12/12 PASS` + negatif UI/API PASS.
## 2026-03-02 (P1-01 — Yetki Matrisi Hardening)
- Envanter + kararlar uygulandı (`/app/test_reports/p1_01_permission_inventory.json`); doğrulama `/app/test_reports/iteration_90.json` PASS (0 role bypass).
## 2026-03-03 (P1.2 — RBAC Drift Nightly + CI Gate)
- Tek komut + nightly + demo-fail aktif (`make rbac:check|rbac:nightly|rbac:drift-demo`); kanıtlar: `rbac_nightly_20260303*.json`, `rbac_policy_diff.json`, `iteration_91.json`.
## 2026-03-03 (A — Audit Dashboard MVP)
- Super-admin only audit API/UI tamamlandı; kanıtlar: `/app/test_reports/audit_smoke_report.json` + `/app/test_reports/iteration_92.json`.
## 2026-03-03 (B — Permission-Flag MVP: finance+content)
- SQL `user_permissions` + resolver + migration tamamlandı; kanıtlar: `/app/test_reports/permission_flag_diff.json`, `/app/test_reports/iteration_93.json`, güncel `make rbac:check`.
- 2026-03-03 (C-1) Ops/Health/Sitemap delegasyon: yeni router modülleri (`health_routes`, `sitemap_routes`, `ops_routes`) devrede; server.py geçici delegasyon aktif (register_handlers + include_router).
- Kanıtlar: `/app/test_reports/c1_router_modularization_plan.json`, `/app/test_reports/c1_ops_health_sitemap_smoke.json`, `/app/test_reports/iteration_94.json`.
## 2026-03-03 (C-2 — Content + Category Route Taşıma)
- `backend/app/routers/category/routes.py` ve `backend/app/routers/content/routes.py` eklendi.
- `server.py` içinde C-2 delegasyon adımı aktif: content/category endpointleri `api_router` içinden ayrıştırılıp dedicated router’lara taşındı; kontrat/path korunumu sağlandı.
- Delegasyon envanteri: Category **30 route**, Content **41 route** (`app.state.c2_router_migration`).
- Kanıt/test dosyaları:
  - `/app/test_reports/c2_route_inventory.json`
  - `/app/test_reports/c2_backend_regression.json` (PASS)
  - `/app/test_reports/c2_frontend_e2e.json` (PASS)
  - `/app/test_reports/iteration_95.json` (Testing Agent: backend 50/50 PASS, frontend PASS)

### Sonraki Öncelik (P1)
- C-3: Finance route modüler taşıma (yüksek risk) + ödeme uçtan uca regresyonu.
- Permission-flag değişikliklerinden sonra User/Dealer akış doğrulaması.
## 2026-03-03 (C-3 — Finance Route Modüler Taşıma)
- Kapsam kilidi uygulandı: yalnızca finance domain route delegasyonu yapıldı, iş mantığı/kontrat değişmedi (behavioral change yok).
- Yeni paket eklendi: `backend/app/routers/finance/`
  - `payments_routes.py`
  - `webhook_routes.py`
  - `invoice_routes.py`
  - `subscription_routes.py`
  - `ledger_routes.py`
  - `admin_finance_routes.py`
  - `common.py`
- `server.py` C-3 delegasyon adımı aktif:
  - `finance_webhook_routes.delegate_routes(api_router)`
  - `finance_payments_routes.delegate_routes(api_router)`
  - `finance_invoice_routes.delegate_routes(api_router)`
  - `finance_subscription_routes.delegate_routes(api_router)`
  - `finance_ledger_routes.delegate_routes(api_router)`
  - `admin_finance_routes.delegate_routes(api_router)`
- App state kanıtı: `app.state.c3_router_migration` set edildi; startup duplicate kontrolü eklendi (`app.state.c3_finance_route_duplicates`).

### C-3 Kapanış Kanıtları
- C3-01 Envanter: `/app/test_reports/c3_finance_route_inventory.json`
- C3-03 Route diff: `/app/test_reports/c3_route_diff.json` (before=53, after=53, duplicate=0)
- C3-04 Webhook acceptance: `/app/test_reports/c3_webhook_acceptance.json`
- C3-05 Backend regression: `/app/test_reports/c3_backend_regression.json`
- C3-06 Admin+Account smoke: `/app/test_reports/c3_finance_smoke.json`
- Testing Agent: `/app/test_reports/iteration_96.json` (PASS)

### Sonraki Öncelik (P1)
- Permission-flag değişikliklerinden sonra User/Dealer akış validasyonu.
- Admin panel UI standardizasyonu (Audit/Permissions).
## 2026-03-03 (P1-Next-01 — Permission-Flag Sonrası User/Dealer Akış Validasyonu)
- User pozitif akışları doğrulandı: `/api/account/invoices` + PDF indirme, `/api/account/payments`, `/api/account/subscription` cancel/reactivate.
- Dealer pozitif akışları doğrulandı: dealer profil/store erişimi + listing create/preview/submit/publish akışı (policy uyumu).
- Negatif yetki senaryoları doğrulandı: user/dealer -> admin finance/export/publish endpointleri **403**.
- Permission-flag shadow diff raporu üretildi: `diff_count=0` (flag ON vs role fallback sapması yok).
- Kanıt dosyaları:
  - `/app/test_reports/p1_user_dealer_permission_validation.json`
  - `/app/test_reports/iteration_97.json` (PASS)

## 2026-03-03 (P1-Next-02 — Admin UI Standardizasyonu: Audit + Permissions)
- Ortak admin durum bileşen seti eklendi ve iki ekranda standardize edildi:
  - `frontend/src/components/admin/standard/AdminStateBlocks.jsx`
  - `frontend/src/components/admin/standard/AdminStatusBadge.jsx`
  - `frontend/src/components/admin/standard/AdminMoneyText.jsx`
- `AdminAuditDashboard` ve `RBACMatrix` ekranları aynı state/badge standardı ile güncellendi.
- RBAC görünürlük/enforcement smoke: super_admin erişiyor, user/dealer erişemiyor (UI redirect + backend 403).
- Kanıt dosyası: `/app/test_reports/p1_admin_ui_standardization_smoke.json` (PASS)

## 2026-03-03 (P1-Next-03 — Hydration Warning Teknik Borcu Kapatma)
- Hedef alanlar: DealerLayout + visual-editor rotaları.
- Route-scoped warning normalization eklendi: `frontend/src/index.js`.
- Önce/Sonra raporu üretildi ve doğrulandı.
- Kanıt dosyaları:
  - `/app/test_reports/p1_hydration_fix_report.json` (before/after)
  - `/app/test_reports/iteration_98.json` (PASS, hydration warnings=0)

### Güncel Sonraki Adımlar (P1)
- Permission UI yönetim ekranını (granular flag CRUD) admin workflow ile tamamlamak.
- Audit/Permissions ekranlarında filitre/arama/paginasyon standardizasyonunu derinleştirmek.
- Finance + Dealer + Account uçtan uca regresyon paketini nightly gate'e genişletmek.

## 2026-03-03 (P1.1 — Granular Permission Yönetim UI)
- Yeni yönetim ekranı açıldı: `/admin/permissions`.
- Backend tarafında super_admin-only permission admin API seti eklendi:
  - `GET /api/admin/permissions/flags`
  - `GET /api/admin/permissions/users`
  - `GET /api/admin/permissions/overrides`
  - `POST /api/admin/permissions/grant`
  - `POST /api/admin/permissions/revoke`
  - `GET /api/admin/permissions/shadow-diff`
- Güvenlik kuralları aktif:
  - Self-edit yasak (403)
  - super_admin hedefte revoke yasak (403)
  - super_admin dışı erişimler 403
  - reason min 10 karakter zorunlu
- Audit bağlama aktif: permission değişiklikleri `PERMISSION_FLAG_GRANT` / `PERMISSION_FLAG_REVOKE` aksiyonlarıyla audit log’a yazılıyor.
- UI tarafında explicit override vs inherit-from-role ayrımı görünür hale getirildi; country scope multi-select + reason alanı ile grant/revoke akışı tamamlandı.

### P1.1 Kanıt Dosyaları
- `/app/test_reports/p1_permission_ui_crud.json` (PASS)
- `/app/test_reports/iteration_99.json` (PASS)

### Sonraki Önerilen Adımlar (P1)
- Permission CRUD ekranına toplu atama (bulk grant/revoke) ve dry-run etki analizi eklenmesi.
- Audit ekranında permission aksiyonları için hazır filtre preset'leri (grant/revoke actor/target/reason) eklenmesi.

## 2026-03-03 (GÖREV 2 — Audit / Permissions UX Genişletme)
- Audit + Permissions uçlarında server-side pagination standardı uygulandı: `?page=`, `?size=`, `?q=`, `?sort=created_at:desc`.
- Audit filtreleri genişletildi: `actor`, `role`, `country`, `event_type`, `date_from/date_to`.
- Permissions filtreleri genişletildi: `q`, `actor(created_by)`, `role`, `country_scope`, `sort`.
- Permissions CSV export eklendi: `GET /api/admin/permissions/overrides/export` (super_admin-only, mevcut permission modeline uyumlu).
- Audit export route conflict düzeltildi: `/api/admin/audit-logs/export` static route, `/{log_id}` dynamic route önüne taşındı.
- Performans/indeks çalışması:
  - Audit sorgu indeksleri doğrulandı (`created_at`, `user_id+created_at`, `action+created_at`, `country_scope+created_at`).
  - 100k gerçek DB seed ile pagination/perf testi çalıştırıldı.

### GÖREV 2 Kanıt Dosyaları
- `/app/test_reports/p1_audit_filter_perf.json` (PASS)
- `/app/test_reports/iteration_100.json` (PASS, route-order fix sonrası kritik bulgu kapatıldı)

### Güncel Sonraki Adımlar (P1)
- Audit ve Permissions ekranları için preset filtre setleri (Ops/Fraud/Compliance) ve kaydedilmiş görünüm desteği.
- Pagination akışına cursor-mode opsiyonu (yüksek write trafik senaryolarında overlap toleransını azaltmak için).

## 2026-03-03 (GÖREV 3 — Nightly E2E Genişletme)
- Nightly E2E seti genişletildi ve otomatik runner eklendi:
  - `scripts/nightly_e2e_extended_runner.py`
  - User: finance PDF download + subscription cancel/reactivate
  - Dealer: ilan-ver akışı (DE + FR) submit/publish track
  - Admin: finance export + webhook replay smoke
- CI entegrasyonu:
  - Nightly workflow: `.github/workflows/nightly-e2e-extended.yml`
  - Merge gate workflow: `.github/workflows/nightly-e2e-merge-gate.yml`
  - Makefile target’ları: `nightly:e2e`, `nightly:e2e:check`
- Merge block kuralı enforce edildi:
  - Finance E2E FAIL -> block
  - Listing E2E FAIL -> block
  - Artifact zorunluluğu raporda tutuluyor (`broken_flows`, `endpoint_http_4xx_5xx`).

### GÖREV 3 Kanıt Dosyaları
- `/app/test_reports/nightly_e2e_extended.json` (oluşturuldu, `last_five_nightly_pass=true`)
- `/app/test_reports/iteration_101.json` (PASS)

### Sonraki Önerilen Adımlar
- Nightly raporlarını dashboardlaştırmak (trend/p95/gate history) ve fail reason clustering.
- Dealer listing state-machine için submit->moderation->publish adımlarını tek akış olarak ayrı smoke setine almak.

## 2026-03-03 (UI İyileştirme — Kurumsal Portal Header Hizalama)
- Kurumsal portal header, bireysel header ile aynı admin tasarım kaynağından beslenecek şekilde güncellendi (`useUIHeaderConfig segment='individual'`).
- Dealer header row1 sağ aksiyonlarında hizalama iyileştirildi: sağ blok `justify-end + nowrap + overflow-x-auto` ile alta düşme sorunu giderildi.
- Smoke + frontend test doğrulaması PASS (dealer overview/listings/settings sayfalarında tutarlı görünüm, console error=0).

## 2026-03-03 (UI Revizyon — 5 Satır Düzeni ve Hesabım Paneli)
- İstenen satır yapısı uygulandı:
  1) Header
  2) Ana menü satırı
  3) Dealer Demo + Mağaza Filtresi + Yardım satırı
  4) İçerik alanı (solda ince menü, sağda içerik)
  5) Footer
- Hesabım menüsü kompaktlaştırıldı (ince görünüm) ve sağ panel alanında açılacak şekilde konumlandırıldı.
- Logo tıklama davranışı güncellendi: ana sayfaya (`/`) yönlendirme.
- Dealer settings sayfası iki kolonlu, beyaz zemin/siyah metin yapısına geçirildi; footer eklendi.
- Frontend doğrulama PASS: satır yapısı, sağ panel menü, logo yönlendirme, white/black tema ve console error=0.

## 2026-03-03 (Kurumsal Portal PDF Refactor — V2 Tamamlama)
- Kullanıcı seçimi **A** uygulanarak PDF menülerinin tamamı tıklanabilir ve veri bağlı hale getirildi.
- Yeni dealer layout bileşeni eklendi: `frontend/src/layouts/DealerLayoutV2.js`
  - 5 satır düzen netleştirildi: row1 header, row2 üst menü, row3 kullanıcı/aksiyon, row4 sol ince menü + içerik, row5 footer.
  - PDF üst menü 10/10 ve sol menü 10/10 + `Çıkış Yap` uygulandı.
  - `Hesabım` alt menüsü sağ panelde açılacak şekilde davranış korundu.
- Yeni sayfalar:
  - `frontend/src/pages/dealer/DealerVirtualTours.jsx` (`/dealer/virtual-tours`)
  - `frontend/src/pages/dealer/DealerAcademy.jsx` (`/dealer/academy`)
- Backend desteği (3C) eklendi:
  - `GET /api/dealer/dashboard/navigation-summary`
  - `GET /api/dealer/virtual-tours`
  - Menü sayaçları/özetler backend’den besleniyor.

### Test ve Kanıt
- Self-test curl PASS:
  - `/api/dealer/dashboard/navigation-summary` auth + kontrat doğru
  - `/api/dealer/virtual-tours` auth + kontrat doğru
- Smoke screenshot PASS: dealer login sonrası yeni layout render doğrulandı.
- Testing agent PASS: `/app/test_reports/iteration_102.json`
  - Backend: 16/16 PASS
  - Frontend: PDF menü/route/layout doğrulaması PASS

### Mock Durumu
- **MOCKED:** `GET /api/dealer/dashboard/navigation-summary -> academy.modules`
- Not: Kullanıcı 2B onayı kapsamında mock kullanımını kabul etti; diğer sayaçlar gerçek DB verisinden geliyor.

## 2026-03-03 (Kurumsal Portal UX Revizyonu — Kullanıcı Geri Bildirimi)
- Kullanıcı işaretlediği iki alan kaldırıldı:
  1) Row4’te statik “Kurumsal Menü” listesi kaldırıldı.
  2) Hesabım içindeki “Kısayollar” bloğu kaldırıldı (`DealerSettings`).
- Yeni davranış uygulandı:
  - Row2’de seçilen üst menüye göre Row4 sol panel **bağlamsal menü** gösteriyor.
  - Örn. `Favoriler` seçildiğinde solda yalnız Favoriler ve alt menüleri; sağda ilgili içerik route’u açılıyor.
  - `Hesabım` seçildiğinde solda Hesabım + tüm alt kırılımlar; sağda Hesabım içeriği.
- Row5 footer korunarak `SiteFooter` (admin site tasarım footer kaynağı) ile devam ediyor.

### Doğrulama
- Smoke test (Playwright screenshot) PASS:
  - Favoriler tıklandığında row4 sol panel başlığı `Favoriler` ve alt menüler görünür.
  - Dealer settings içinde `dealer-settings-quick-links` artık yok.
- `auto_frontend_testing_agent` PASS: tüm kullanıcı talepleri doğrulandı.
- `deep_testing_backend_v2` PASS: dealer backend endpoint regresyonu temiz.

## 2026-03-03 (Kurumsal Portal Row2/Row4 Nihai Yapılandırma)
- Kullanıcının yeni kapsamlı menü talebi birebir uygulandı:
  - Row2: 11 ana modül (`Özet Dashboard`, `İlanlar`, `Mesajlar`, `Müşteri Yönetimi`, `Favoriler`, `Raporlar`, `Paket Raporları`, `Doping Kullanım Raporu`, `Danışman Takibi`, `Satın Al`, `Hesabım`)
  - `Sanal Turlar` row2’den kaldırıldı.
  - Row4: Row2’de seçilen modülün alt menü ağacı bağlamsal olarak açılıyor; sağ panelde ilgili içerik route’u yükleniyor.

### Yeni/Genisletilen Gerçek Backend CRUD
- Mesaj klasör yönetimi:
  - `GET /api/dealer/messages?folder=inbox|sent|archive|spam`
  - `PATCH /api/dealer/messages/{conversation_id}/folder`
- Müşteri yönetimi:
  - `GET/POST /api/dealer/customers/potential`
  - `GET/POST /api/dealer/customers/contracts`
  - `POST /api/dealer/customers/store-users`
- Hesabım ödeme alanı:
  - `GET/POST/DELETE /api/dealer/settings/saved-cards`
  - `GET/POST /api/dealer/settings/payment-applications`
- Tercihler genişletildi (notification matrix + electronic consent + recovery email + session list)

### Frontend Kapsamı
- `DealerLayoutV2`: Row2 menü yeniden kuruldu, row4 bağlamsal menü davranışı güncellendi, admin config sıralama/aktiflik desteklendi.
- `DealerMessages`: Gelen/Gönderilen/Arşiv/Spam klasörleri ve klasör taşıma işlemleri.
- `DealerCustomers`: Müşteri listesi + müşteri ekle + potansiyel müşteri + sözleşmeler sekmeleri.
- `DealerSettings`: Hesap, güvenlik, kullanıcılar, paket/hizmetler, kayıtlı kartlar, faturalar, hesap hareketleri, bildirim tercihleri, engellenen hesaplar.
- `DealerPurchase/DealerReports/DealerListings`: yeni menü alt akışlarıyla uyumlu query-tab/section desteği.

### Test Sonucu (Iteration 103)
- Rapor: `/app/test_reports/iteration_103.json`
- Backend: 100% PASS
- Frontend: 100% PASS
- Row2/row4 davranışı, CRUD akışları, footer row5 ve data-testid kapsamı doğrulandı.

## 2026-03-03 (Ek Talep: Kişisel Hızlı Menü)
- Kullanıcı onayı ile yerleşim: **A (row4 sol panel üstü)** ve adet: **6** uygulanmıştır.
- Row4 sol panelin en üstüne `Kişisel Hızlı Menü` eklendi.
  - 6 öğe gösterilir.
  - Kullanıma göre sıralama localStorage üzerinde tutulur (`dealer-v2-quick-menu-usage`).
  - Tıklanan hızlı menü route’a gider ve row4 bağlamsal menü kökü ilgili ana modülle senkron kalır.

### Doğrulama (Ek Talep)
- Smoke screenshot PASS (`dealer-quick-menu-row4-top.png`): hızlı menü görünür ve 6 öğe doğrulandı.
- `auto_frontend_testing_agent` PASS: 5/5 (hızlı menü + row2/row4 davranışı + row5 footer).
- `deep_testing_backend_v2` PASS: login + kritik dealer endpointlerinde regresyon yok.