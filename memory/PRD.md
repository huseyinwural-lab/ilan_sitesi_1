# FAZ Admin Domain Complete — PRD

**Son güncelleme:** 2026-02-19 (Dashboard v2 genişletmesi)

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
- **Kategori Sihirbazı P0 Stabilizasyonu (2026-02-19):**
  - Detay grubu state tek kaynak + checkbox listesi 4’lü grid
  - Modüller: Adres/Fotoğraf/İletişim/Ödeme + key badge + kaynak etiketi
  - Modül bağımlılıkları (payment off → paket/doping pasif + collapse, photos on → foto limit görünür)
  - Taslak kaydet tüm adımlar + publish guard (hierarchy/core/2a/2c)
  - Preview gate: özet + modül listesi + uyarı listesi + JSON accordion
  - Backend kategori payload: hierarchy_complete + form_schema alanları
- **Preview Gate Acceptance Criteria (UI/UX):**
  - Şema özeti + modül listesi + validation uyarıları görünür (zorunlu)
  - JSON schema accordion (default kapalı) + salt okunur / debug etiketi
  - “Önizlemeyi Onayla” ile publish aktifleşir
  - Publish butonu preview tamamlanmadan pasif kalır
- **FAZ-7 Admin Login Stabilizasyonu:**
  - GET /api/admin/session/health (token doğrulama + expires_at)
  - Sidebar bootstrap health-check sonrası render
  - Playwright admin login smoke testi (dashboard → kategoriler)
  - Test yolu: /app/frontend/tests/e2e/admin-login.spec.js
- **FAZ-7 Auth Edge-case Test Report (2026-02-19):**
  - Expired token health-check → 401 + UI logout doğrulandı
  - Multi-tab logout → ikinci sekme login ekranına düştü
  - Test yolu: /app/frontend/tests/e2e/admin-auth-edge.spec.js
- **Kategori Sihirbazı Full E2E (2026-02-19):**
  - Hierarchy → Core → 2a → 2c → Modules → Preview → Draft → Publish akışı
  - Draft/Publish API assertion’ları
  - Admin wizard senaryosu aktif; user listing senaryoları fixture tamamlanınca açılacak
  - Playwright baseURL standardı: PLAYWRIGHT_BASE_URL (varsa) → REACT_APP_BACKEND_URL (.env)
  - Test yolu: /app/frontend/tests/e2e/schema-e2e.spec.js
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

## Release Notes
- Dashboard summary gerçek veriye bağlandı + Quick Actions aktif (users/countries/audit)
- Dashboard canlı veri + Quick Actions + E2E PASS (Dashboard fazı kapatıldı)
- Dashboard health: uptime + restart zamanı eklendi
- Dashboard summary endpoint (/api/admin/dashboard/summary) + RBAC + cache
- 2026-02-19: Dashboard v2 KPI (Bugün/Son 7 Gün) + trend grafikleri (ilan/gelir)
- 2026-02-19: Risk & alarm paneli (çoklu IP/SLA/bekleyen ödeme) + sistem sağlığı gecikme metrikleri
- 2026-02-19: Finans verileri RBAC (sadece finance/super_admin) + /admin ve /admin/dashboard birleşik görünüm
- Yeni /admin/audit route + AdminRouteGuard (403)
- Preview PDF/CSV Export + E2E PASS (Export fazı kapatıldı)
- Export modülü freeze (yeni geliştirme yok)
- Admin imzası backlog’a alındı (sonraki faz)

## Öncelikli Backlog
### P0 (Sıradaki)
- (Boş) — Preview gate + FAZ-7 auth kontrolleri + wizard E2E tamamlandı

### P1
- Lint debt cleanup (LINT-1/2)
- Runtime config / feature flag (Dashboard TTL yönetimi) — backlog

### P2
- Versioning diff highlight + rollback (aktif faz)
- Lint debt cleanup (LINT-3/4/5)
- Şema versiyonlama + audit log sertleştirme

### P3
- Admin imzası (export rapor imzası) — backlog
- Dinamik modül adımları (ilan verme sihirbazında modül bazlı step)

## Lint Debt Roadmap (Backend)
- LINT-1: F821 build_audit_entry undefined (server.py:1236/1283) → import veya helper ekle
- LINT-2: F841 unused variable `v` (server.py:2466) → kaldır
- LINT-3: E741 ambiguous `l` (server.py:2639/2642) → anlamlı isimle değiştir
- LINT-4: F601 duplicate "$or" key (server.py:4798) → query birleştir
- LINT-5: F821 now_iso undefined (server.py:5126) → timestamp kaynağını standardize et
- Plan: P1’de LINT-1/2, P2’de LINT-3/4/5 + lint CI gate (baseline bozulmasın)
- Not: Frontend ESLint gate şu an “legacy uyumlu” (no-unused-vars/no-undef kapalı); P2’de kademeli sıkılaştırma

## P2 Spec — Versioning Diff + Rollback (Active)
- Amaç: Admin’in yayın öncesi değişiklikleri sürüm bazında görmesi ve diff karşılaştırması
- Gerekli API’ler:
  - GET /api/admin/categories/{id}/versions (list)
  - GET /api/admin/categories/{id}/versions/{version_id} (detail + snapshot)
  - POST /api/admin/categories/{id}/versions/{version_id}/rollback (draft olarak aç)
  - POST /api/admin/categories/{id}/publish (publish sonrası yeni version)
- E2E Planı:
  - draft → publish → yeni versiyon oluştuğunu doğrula
  - rollback endpoint ile önceki versiyona dön → taslak açıldığını doğrula
  - yeniden publish → version artışını doğrula
- UI: Versiyon listesi + iki versiyon diff highlight + rollback CTA
- Diff highlight: added/removed/changed (required/messages/options/modules)
- Rollback: sadece admin + audit log zorunlu
- Risk/Önlem: Draft şişmesi → versiyon limiti (örn. son 25)

## Autosave Spec (P1)
- Draft modunda event-driven autosave: field change → 2.5s debounce → draft save
- Autosave sadece `status=draft` iken aktif; publish sonrası pasif
- Toast durumları: “Kaydediliyor…”, “Taslak kaydedildi”, “Kaydetme başarısız”
- Preview header: “Son kaydetme: HH:mm:ss”
- Optimistic locking: `expected_updated_at` ile 409 conflict → “Başka bir sekmede güncellendi” toast
- Sayfadan çıkışta tek seferlik flush save (keepalive/sendBeacon)

## Preview Export Mini-Spec (P1)
- PDF export zorunlu; preview gate onayı sonrası üretilecek
- CSV export opsiyonel (sadece modül + alan listesi, sadeleştirilmiş)
- İçerik: kategori özeti, modül listesi, dinamik alanlar, detay grupları, validation uyarıları, timestamp
- Yetki: super_admin + country_admin
- Formatlar: PDF (tam rapor), CSV (modül/alan matrisi)
- Not: Export snapshot, preview-onaylı schema üzerinden üretilecek
- Rate limit: 10 istek / 60 sn (admin başına)
- Audit_logs event_type index: mevcut + (event_type, created_at) composite index

## P1 Tasarım Dokümanları
- Draft Versioning + Diff MVP: /app/memory/DESIGN_DRAFT_VERSIONING.md


## Appendix: P0 Stabilizasyon Final Raporu
### Kapsam
- Preview Gate zorunlu adım + publish enablement
- Auth edge-case testleri (expired token + multi-tab logout)
- Kategori sihirbazı E2E (admin wizard + draft/publish)
- Playwright baseURL standardizasyonu (PLAYWRIGHT_BASE_URL → REACT_APP_BACKEND_URL)

### Değişiklik Listesi
- Preview adımında özet + modül listesi + validation uyarıları + JSON accordion
- Draft/Pubish API assertion’lı wizard E2E senaryosu
- FAZ-7 auth edge-case Playwright senaryoları
- Wizard step unlock fix: hierarchy_complete backend flag ile guard + draft save sonrası refetch
- Step navigation guard: sekmeler default disabled, “Tamam” ile unlock + tooltip
- Hiyerarşi kriteri: ana ad + slug + en az 1 alt kategori
- Lint debt yol haritası ve versiyonlama tasarım başlangıcı
- Unlock state tek kaynak: isHierarchyComplete only, persist sonrası unlock
- Admin Kategoriler ekranı metin kontrastları koyulaştırıldı
- E2E fixture kullanıcı + fixture kategori şeması seed edildi (user@platform.com)
- v2 vehicle makes/models endpoint alias eklendi (wizard test stabil)
- Preview export (PDF/CSV) endpoint + audit log + rate limit eklendi
- Preview adımına PDF/CSV indir butonları eklendi
- Export E2E doğrulamaları (content-type + dosya adı) eklendi

### Test Kanıtı
- playwright: tests/e2e/admin-auth-edge.spec.js → ✅ 2 test geçti
- playwright: tests/e2e/schema-e2e.spec.js → ✅ Senaryo 1/2/3 geçti
- UI regresyon: auto_frontend_testing_agent ✅

### Fixture Durumu
- user@platform.com (role: individual) seed ✅
- Published fixture kategori şeması ✅
- Vehicle master data (make/model) seed ✅

### Risk / Önlem
- Risk: Export/PDF gelecekte schema ile uyumsuz olabilir → snapshot tabanlı üretim şartı

### Kapanış Kriterleri
- Preview Gate yayın öncesi zorunlu
- Auth edge-case testleri yeşil
- Wizard E2E Senaryo 1 (draft+publish) yeşil
- P0 kapsamında açık blocker kalmaması
