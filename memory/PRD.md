# FAZ Admin Domain Complete — PRD

**Son güncelleme:** 2026-02-19 (Kategori Sihirbazı Stabilizasyonu)

## Program Status (23.02.2026)
- Foundation Phase: **OFFICIALLY CLOSED**
- Release Gate: **OFFICIALLY CLOSED**
- Production Activation: **OFFICIALLY CLOSED**
- Hypercare: **OFFICIALLY CLOSED**
- Launch: **ACTIVE**

## Orijinal Problem Tanımı
Çok ülkeli, çok dilli bir seri ilan platformunda (Public, Dealer, Backoffice/Admin) **admin domainindeki tüm “yakında” modüllerin** gerçek veriler ve tam işlevsellikle hayata geçirilmesi. Tüm admin mutasyonları **audit-first** ve **country-scope** kurallarına uymalıdır.

## Hedefler
- Admin panelinde tüm kritik alanların (Bayiler, Başvurular, İlanlar, Finans, Sistem, Master Data) canlı veriyle yönetilebilmesi
- Country-scope ile ülke bazlı yetkilendirme
- Audit-first standartlarında denetim kayıtları

## Kullanıcı Personaları
- **Super Admin:** Global yetkili yönetici
- **Country Admin:** Ülke bazlı yetkili yönetici
- **Moderator:** Moderasyon işlemleri
- **Dealer:** Bayi hesabı

## Temel Gereksinimler
- URL tabanlı country context (`?country=XX`)
- Tüm admin mutasyonlarında audit-first kayıt zorunluluğu
- Rol tabanlı erişim (RBAC)
- Çok dilli UI (TR/DE/FR)

## Mimari
- **Frontend:** React (portal bazlı code-splitting)
- **Backend:** FastAPI
- **Database:** MongoDB (motor)
- **Portallar:** Public / Dealer / Backoffice
- **Kritik Koleksiyonlar:** `users`, `dealer_applications`, `vehicle_listings`, `audit_logs`, `categories`, `countries`

## Uygulanan Özellikler
- **Sprint 0:** Admin domain şema ve audit-first standardı
- **Sprint 1.1:** Bayi Yönetimi (listeleme + durum değiştirme)
- **Sprint 1.2:** Bayi Başvuruları (listeleme + onay/red akışı)
- **Sprint 2.1:** Admin Global Listing Yönetimi
  - Filtreler: country-scope, status, search, dealer_only, category_id
  - Aksiyonlar: soft-delete, force-unpublish
- **Sprint 2.2:** Reports Engine (Şikayet Yönetimi)
  - Report reason enum + lifecycle
  - Admin list/detail/status API + audit-first
  - Public report submit (rate limit)
  - Admin UI /admin/reports + listing detail “Şikayet Et”
- **Sprint 3:** Finance Domain
  - Invoice Engine: create/list/detail/status + revenue endpoint
  - TaxRate CRUD (audit-first)
  - Plan CRUD (audit-first)
  - Dealer plan assignment (users.plan_id) + dealer detail finance summary
  - Admin UI: /admin/invoices, /admin/tax-rates, /admin/plans
- **Sprint 4:** System + Dashboard
  - Country CRUD (country_code PK, audit-first)
  - System Settings KV + effective view
  - Dashboard KPI API (summary + country compare)
  - Admin UI: /admin/countries, /admin/system-settings, /admin/dashboard, /admin/country-compare
- **Sprint 5:** Master Data Engines
  - Category + Attribute + Vehicle Make/Model CRUD (audit-first)
  - Search filtreleri master data’dan (category/make/model)
  - Admin UI: /admin/categories, /admin/attributes, /admin/vehicle-makes, /admin/vehicle-models
- **Kategori Form Şablonu v2:**
  - Core fields: başlık/açıklama/fiyat + EUR/CHF + input masking + secondary currency
  - Dynamic fields (2a) + detail groups (2c) + sabit modüller (adres/foto/iletişim/ödeme)
  - Validation mesajları + duplicate title toggle + schema publish guard
  - Frontend listing wizard schema tabanlı form üretimi
  - Public contract: /api/catalog/schema?category_id=...&country=...
- **FAZ-7 Admin Login Stabilizasyonu:**
  - GET /api/admin/session/health (token doğrulama + expires_at)
  - Sidebar bootstrap health-check sonrası render
  - Playwright admin login smoke testi (dashboard → kategoriler)
  - Test yolu: /app/frontend/tests/e2e/admin-login.spec.js
- **Admin Kategori Modal Kontrast Düzeltmesi:**
  - Modal input/label/placeholder renkleri koyu tona çekildi (WCAG uyumlu)
  - Playwright görsel regresyon testi eklendi
- **Sprint 6:** Final Integration Gate
  - RBAC + Country-scope + Audit coverage kanıtları
  - Kritik akışlar E2E (public/dealer/individual/report/finance)
  - Non-functional kontroller (empty/403/404/draft erişim)
  - Finance RBAC sıkılaştırma + publish guard uyumu
- **Admin IA v2:** Sol menü bilgi mimarisi yeniden yapılandırma + RBAC görünürlük matrisi
- **Admin UI v1:** Admin kullanıcıları, rol tanımları, RBAC matrix (read-only) + placeholder ekranlar + nav smoke
- **Admin Nav Smoke:** Menü route doğrulaması (Playwright)
- **Admin UI v1 Closeout:** Evidence pack + RC checklist güncellendi
- **Yönetim Menüsü:** Admin/roles/RBAC menüleri aktif ve “yakında” etiketi kaldırıldı
- **Bireysel Üye Başvuruları:** Admin liste + approve/reject akışı aktif
- **İlan Başvuruları:** Moderation Queue filtreleriyle bireysel/kurumsal başvuru sayfaları aktif
- **Menü Yönetimi:** CRUD + audit-first + country-scope aktif
- Moderation Queue + audit log altyapısı
- Login rate-limit ve audit log (FAILED_LOGIN, RATE_LIMIT_BLOCK)

## Öncelikli Backlog
### P0 (Sıradaki)
- P1 sprint başlangıç tarihi netleştirme

### P1
- **Backlog:** P1 sprint planlama + kickoff
- **Backlog:** Admin Listing Preview Drawer
- **Backlog:** Bulk Report Status Update
- **Backlog:** Finance CSV Export
- **Backlog:** Revenue Chart
- **Backlog:** Dashboard View Audit
- **Backlog:** Master Data CSV Import/Export
- **Backlog:** Audit Dashboard Widget (Son 24 Saat Kritik Event)
- **Backlog:** Kampanyalar CRUD + uygulama noktaları
- **Backlog:** Billing/Ödeme kayıtları entegrasyonu

### P2
- V3 genişletmeler (gelişmiş arama, güven katmanı, bayi genişletmeleri)
