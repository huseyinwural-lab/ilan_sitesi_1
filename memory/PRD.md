# FAZ Admin Domain Complete — PRD

**Son güncelleme:** 2026-02-21 (Invoices V1 + Campaigns/Plans)

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
- **Database:** MongoDB (legacy) + Postgres (geçiş)
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
- **Bireysel Portal Faz B1-B7 (2026-02-20):** /account IA + role guard, bireysel menü standardı, listing wizard 5 adım, draft kaydet, my listings filtre/aksiyonlar, moderasyon notu görünümü, favorites/messages/support list/detail, profil/şifre ekranı
- **B8.1-B8.4 (2026-02-20):** Favoriler backend + profil/şifre API + GDPR export (metadata-only) + mesajlaşma REST/WS + push subscription altyapısı (VAPID secrets bekliyor)

## Release Notes
- 2026-02-21: Local Postgres native kuruldu; alembic upgrade heads PASS; Stripe checkout async fix + webhook imza testleri ile payment zinciri local E2E PASS; p30_user_quota_limits + p31_listing_contact_options migration eklendi; FINAL01_LOCAL_E2E kanıtı üretildi.
- 2026-02-23: Email provider switch (EMAIL_PROVIDER mock/smtp/sendgrid) + retention policy/job spec dokümanları + verification email prod switch wiring tamamlandı.
- 2026-02-23: Email verification prod switch hazırlandı (p29 token table, TTL=15dk, debug_code kaldırıldı) + frontend debug alanları temizlendi.
- 2026-02-23: Health endpoint reason/db_status eklendi; Stripe checkout stub + webhook DB-blocked response hazırlandı; UNBLOCK checklist evidence path eklendi; EMAIL_VERIFICATION_SWITCH + Ad Wizard mapping checklist dokümanları eklendi.
- 2026-02-23: FINAL-01 order lock + Mongo cutoff (config + auth fallback removal), BLOCKED/UNBLOCK runbook’ları eklendi.
- 2026-02-23: ADR-MIG-01 enforced (migrations README güncellendi), DB Migration Evidence Pack eklendi; local Postgres servisi olmadığı için Alembic upgrade/current kanıtları **BLOCKED**.
- 2026-02-21: Invoices V1 (schema + migration + SQL admin list + state machine + simülasyon + EXPLAIN) + BILLING_V1_LOCK.md kilidi. Mongo invoice referansları kaldırıldı.
- 2026-02-21: Monetization Chain başlangıcı: Campaigns Schema V1 (migration + SQL CRUD + audit SQL), Campaigns backfill raporu, Plans period alanı + default plan seed (3×2), Billing status V1 standardizasyonu, Webhooks V1 dokümanı, Admin Plans UI period kolonu + /admin/campaigns redirect + Campaigns UI rules_json uyumu.
- 2026-02-21: Notifications SQL V1 tamamlandı (schema + endpoints + backfill + decommission/gate dokümanları). Alembic `upgrade heads` uygulandı, `/api/health` healthy, `/api/auth/login` 520 RCA + fix, Notifications E2E PASS.
- 2026-02-21: AUTH1.8 inline register doğrulama (tek sayfa OTP, auto login), login doğrulama engeli + verify endpoint token dönüşü.
- 2026-02-21: Email doğrulama altyapısı (AUTH1.7): users doğrulama alanları + /api/auth/verify-email ve /api/auth/resend-verification + verify-email UI (OTP, cooldown, debug_code) + login gating.
- 2026-02-21: Register route haritası (\"/register\", \"/dealer/register\"), consumer/dealer kayıt formları, /api/auth/register/consumer|dealer ve /api/countries/public endpointleri eklendi; dealer profile slug migration (p27).
- 2026-02-21: Login banner metni Annoncia olarak güncellendi, reCAPTCHA metni kaldırıldı, beyaz zemin yazı kontrastı iyileştirildi.
- 2026-02-21: Tek giriş sayfası (bireysel/ticari seçimli), turuncu zeminli login UI + portal uyumsuzluk kontrolü; /login ve /dealer/login ortak.
- 2026-02-21: Dealer Listings FAZ-DL2 bulk actions (archive/soft delete/restore) + status filtre (default active) + bulk response failed count; evidence: /app/docs/DEALER_LISTINGS_BULK_EVIDENCE.md.
- 2026-02-21: Dealer dashboard metrikleri (active listings + quota + views + messages + plan card) eklendi.
- 2026-02-21: Dry-run PDF raporu (özet + field-level diff + kritik uyarılar + schema snapshot) eklendi.
- 2026-02-21: Category import/export V1.1 (field-level diff + dry-run hash gating + critical warning banner + pagination).
- 2026-02-21: Categories import/export modülü eklendi (JSON+CSV, dry-run + commit + batch publish).
- 2026-02-21: Categories SQL migration tamamlandı (public + admin CRUD + schema versions + seed script).
- 2026-02-21: MONGO_TO_SQL_MIGRATION_V1 dokümanı + favorites/support_messages için Alembic draft hazırlandı.
- 2026-02-21: SQL messaging planı (conversations/messages) dokümana işlendi; draft tablo çakışması giderildi.
- 2026-02-21: Admin dashboard summary Mongo yokken boş veri döner; admin countries 200 + boş liste.
- 2026-02-21: AdminUsers filtreleri custom dropdown + div-based liste (hydration warning fix).
- 2026-02-21: Dealer portal listing CRUD (SQL) + quota chip + yeni route/menü.
- 2026-02-21: Mongo bağımlılık envanteri oluşturuldu (/app/architecture/MONGO_DEPENDENCY_AUDIT.md).
- 2026-02-21: Local Postgres dev (.env.local) + SQL auth/app providers aktif; migrations (heads) başarıyla uygulandı; admin/dealer/consumer seed kullanıcılar oluşturuldu.
- 2026-02-21: portal_scope token v2 + websocket scope check; /health/db localhost 200; Account portal turuncu tema doğrulandı.
- B8: Favoriler backend + profil/şifre API + GDPR export + mesajlaşma REST/WS entegrasyonu + push subscription altyapısı (VAPID secrets bekliyor)
- Bireysel Portal: /account IA + guard + listing wizard (5 adım) + my listings aksiyonları + favorites/messages/support/profil temel akışlar
- Dashboard summary gerçek veriye bağlandı + Quick Actions aktif (users/countries/audit)
- Dashboard canlı veri + Quick Actions + E2E PASS (Dashboard fazı kapatıldı)
- Dashboard health: uptime + restart zamanı eklendi
- Dashboard summary endpoint (/api/admin/dashboard/summary) + RBAC + cache
- 2026-02-19: Dashboard v2 KPI (Bugün/Son 7 Gün) + trend grafikleri (ilan/gelir)
- 2026-02-19: Risk & alarm paneli (çoklu IP/SLA/bekleyen ödeme) + sistem sağlığı gecikme metrikleri
- 2026-02-19: Finans verileri RBAC (sadece finance/super_admin) + /admin ve /admin/dashboard birleşik görünüm
- 2026-02-19: Trend aralığı filtresi (7-365) + Dashboard PDF export (super_admin)
- 2026-02-19: Country compare analitik genişletme (growth %, conversion, dealer density, SLA 24/48, risk, bar chart + heatmap)
- 2026-02-19: Country compare tarih filtresi + ECB EUR normalizasyonu (24h cache + fallback) + CSV export + E2E test
- 2026-02-19: Countries seed düzeltmesi (DE/CH/AT/FR aktif, PL pasif) + country-compare varsayılan filtre (DE/CH/AT)
- 2026-02-19: Admin Countries ISO dropdown + arama (i18n-iso-countries) ile yeni ülke ekleme (locale/currency alanları)
- 2026-02-20: Admin kullanıcı yönetimi (listeleme, filtre/sıralama, edit modal, bulk deactivate)
- 2026-02-20: Admin davet akışı (SendGrid entegrasyonu + /admin/invite/accept şifre belirleme)
- 2026-02-20: Admin RBAC güvenlik kontrolleri + audit log olayları (admin_invited/accepted/role_changed/deactivated)
- 2026-02-20: Admin kullanıcıları IA temizliği (Kullanıcı Yönetimi menüsü kaldırıldı, /admin/users & /admin/user-management redirect)
- 2026-02-20: Admin silme (soft delete + silinenler filtresi + admin_deleted audit)
- 2026-02-20: Bireysel kullanıcılar ekranı (SSOT individual filtre, soyad A→Z varsayılan sıralama, server-side arama + sayfalama)
- 2026-02-20: Bireysel kullanıcı demo seed (6 kullanıcı, phone_e164) + telefon araması + CSV export
- 2026-02-20: Kurumsal kullanıcılar standardizasyonu (dealer listeleme + filtre/sıralama + moderasyon aksiyonları + audit + hızlı drawer)
- 2026-02-20: Moderasyon şablonları (Spam/Dolandırıcılık/Müstehcen/Sahte ilan/Tekrarlı ihlal) + otomatik reason_detail
- 2026-02-20: Başvuru Modülü P0 (RDBMS applications tablosu + /api/applications create/list + admin assign/status + rate limit + XSS sanitize + URL validation) — DB bağlantısı gerekli
- 2026-02-20: DB gate rollback (fail-fast kaldırıldı, fallback geri geldi, /health/db soft-degraded)
- 2026-02-20: Mongo Exit P0 hazırlık dokümanları (inventory + schema + ops runbook) + auth migration seti
- 2026-02-20: Auth + Applications repository abstraction (mongo/sql provider switch) + MONGO_ENABLED kill switch
- 2026-02-20: APP_ENV=prod strict fail-fast guard (prod strict, preview/dev degraded)
- 2026-02-20: Support formu (KVKK + dosya URL mock + ilan ID) + admin başvuru listesi filtre/kolon güncellemesi
- 2026-02-20: Preview ortamında /health/db backend 503 döndürüyor; edge katmanında 520 görülüyor (proxy passthrough gerektirir)
- 2026-02-20: Postgres secret hazır değil; SQL provider aktif değil (Mongo fallback sürüyor)
- Yeni /admin/audit route + AdminRouteGuard (403)
- 2026-02-20: Deploy gate script (deploy_gate_check.py) + GitHub Actions deploy-prod workflow eklendi
- 2026-02-20: Kampanyalar menüsündeki Şikayetler alt menüsü kaldırıldı (işlevsiz)
- 2026-02-20: Kampanyalar V1 (campaigns tablosu/migration + admin CRUD + UI placeholder kaldırma + pricing read-path tasarımı)
- 2026-02-20: Vehicle Type V1 (taxonomi + vehicle_models vehicle_type zorunlu + admin UI filtre/kolon + import dry-run/apply endpoint + örnek JSON)
- 2026-02-20: CQA Offline Package V1 (zip envanter + mapping/normalizasyon dokümanları + vehicle/attribute import JSON + transform raporu)
- 2026-02-20: Plans Admin V1 hazırlıkları (DB gate banner/disable, yeni UI filtreleri ve form, plans SQL model + migration + Postgres API kontratı)
- 2026-02-20: Plans UI P1 (scope quick filter chip + updated sort kısayolu)
- 2026-02-20: Invoices Admin V1 hazırlıkları (UI filtre/kolon genişletme + DB gate disable + Postgres admin invoice modeli + p25 migration + API kontratı)
- 2026-02-20: Invoices UI P1 (Son 7/30 gün quick date preset + temizle)
- 2026-02-20: Payments Stripe V1 hazırlıkları (payments/admin_invoices payment_status migration + Stripe checkout/webhook endpoints + dealer invoices UI + success/cancel pages + admin payments list)
- 2026-02-20: Invoice UI badges (dealer + admin invoice/payment status badges + tooltips)
- 2026-02-20: Admin login fix (payment model import cleanup + metadata column rename; backend startup restored)
- 2026-02-20: Audit Logs V1 (admin UI filtre/sıralama/detay/CSV export + ROLE_AUDIT_VIEWER RBAC + DB gate banner/disable)

- Preview PDF/CSV Export + E2E PASS (Export fazı kapatıldı)
- Export modülü freeze (yeni geliştirme yok)
- Admin imzası backlog’a alındı (sonraki faz)

## Öncelikli Backlog
### P0 (Sıradaki)
- FAZ-FINAL-01 Critical User Path: **AUTH → Stripe → Ad Loop** (order lock)
- Local E2E kanıtı: `/app/ops/FINAL01_LOCAL_E2E.md`
- AUTH SQL full migration + Mongo cutoff + Auth E2E
- Stripe Payment zinciri: Payments V1 unique + webhook idempotency/replay + invoice/subscription/quota chain
- Ad Loop E2E: ilan oluştur → medya → publish → public görünür
- Email verification prod switch: token tablosu + unique index + TTL=15dk + debug kaldırma
- Ad wizard SQL mapping gap fix: category_id + make_id/model_id mapping
- Ops: DATABASE_URL secret (preview/prod) + migration/seed
- Local Postgres UNBLOCK **PASS** (FINAL01_LOCAL_E2E.md). Preview/prod DB hala BLOCKED.
- Billing audit log tablo adı net değil (billing_audit_log yok; audit_logs kullanılıyor) → netleştirilecek.
- Public search + moderation hâlâ Mongo (Ad Loop public görünürlük staging’de doğrulanacak).
### P1
- Verification token cleanup job (00:30 UTC) + retention policy (24h/7d) kanıtları
- Lint debt cleanup (LINT-1/2)
- Runtime config / feature flag (Dashboard TTL yönetimi) — backlog
- Başvuru Modülü bildirimleri (in-app + email) — P1
- Consumer Portal B8: E2E senaryoları (ilan oluştur/yayınla/düzenle, favori, mesaj, ticket)

### P2
- Notifications UI: badge + okunmamış/tür filtreleri (Medium priority, Monetization sonrası)
- Admin kullanıcı yönetimi audit log sertleştirme (admin_role_changed/admin_scope_changed/admin_suspended/admin_activated/admin_invited) + before/after metadata
- Admin kullanıcı yönetimi için E2E test paketi (rol/scope değişimi, last super_admin koruması, 403 görünmez aksiyonlar)
- Bireysel kullanıcılar arama/sıralama için index önerisi: last_name + first_name + email + phone_e164 (text/compound)
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
