# FAZ EU Panel — PRD

**Son güncelleme:** 2026-02-24 17:50:00 UTC (AF Sprint1 migration impact)

## Orijinal Problem Tanımı
EU uyumlu **Consumer** ve **Dealer** panellerinin tasarlanması ve geliştirilmesi.
GDPR/KVKK kapsamı gereği profil yönetimi, privacy center, 2FA ve veri minimizasyonu zorunlu.
Mongo **kullanılmayacak**; tüm yeni geliştirmeler PostgreSQL + SQLAlchemy üzerinden ilerleyecek.

## Hedefler
- Consumer ve Dealer profillerinin ayrıştırılması (consumer_profiles / dealer_profiles)
- GDPR Privacy Center (JSON export + soft delete + consent log)
- 2FA (TOTP + Backup codes)
- EU uyumlu şirket profili ve VAT doğrulama (regex)
- Preview/Prod ortamlarında DB fail-fast + migration gate
- Register anti-bot + GDPR export bildirimleri
- Ops görünürlüğü (ops_attention + last_db_error)
- EU uyumlu portal navigasyonu (TR/DE/FR)
- İlan ver sihirbazı tamamlanması (test-id kapsamı)

## P0 Kapsam Kilidi (Admin Kategori Sihirbazı)
- Akış düzeltmesi (Tamam→PATCH, Next gating + tooltip)
- Backend authoritative wizard_progress
- E2E test paketi (Frontend+Backend)
- Preview DB env workaround notu (yalnız preview, prod/stage yasak)

### P1 (Beklemede)
- Public Search & Moderation Mongo→PostgreSQL

### P2 (Plan)
- Kayıtlı Arama/Alert (P2 backlog)
- Parametre Alanları tabı
- VIES VAT doğrulama
- GDPR CSV export
- Moderation reject flow
- Scheduled token cleanup

## Kullanıcı Personaları
- **Consumer (Bireysel)**
- **Dealer (Kurumsal)**

## Temel Gereksinimler
- Consumer Profile: full_name, display_name_mode, locale, country_code, marketing_consent
- Dealer Profile: company_name, vat_id, trade_register_no, authorized_person, address_json, logo_url
- Privacy Center: JSON export, consent logging, soft delete (30 gün grace)
- 2FA: TOTP + recovery/backup codes
- RBAC: Consumer/Dealer ayrımı

## Mimari
- **Frontend:** React (Account/Dealer portal)
- **Backend:** FastAPI (server.py monolith + SQLAlchemy)
- **Database:** PostgreSQL (DATABASE_URL)
- **Mongo:** EU panel sprintlerinde devre dışı (MONGO_ENABLED=false)

## ADR Referansları
- /app/memory/ADR.md (tek kaynak)

## Uygulanan Özellikler
- EU panel dokümantasyon paketi (/app/docs/CONSUMER_IA_V1.md, DEALER_IA_V1.md, PRIVACY_CENTER_EU.md, DATA_MODEL_SPEC_EU_PROFILES_V1.md)
- ConsumerProfile ve DealerProfile modelleri
- DealerProfile için gdpr_deleted_at alanı (model + migration: p34_dealer_gdpr_deleted_at)
- Helper: lazy create + VAT regex doğrulama + profile response builder
- **Yeni v1 endpointler:**
  - GET/PUT /api/v1/users/me/profile (consumer)
  - GET/PUT /api/v1/users/me/dealer-profile (dealer)
  - GET/PUT /api/v1/dealers/me/profile (alias)
  - GET/POST /api/v1/users/me/2fa/* (status/setup/verify/disable)
  - GET /api/v1/users/me/data-export (JSON)
  - DELETE /api/v1/users/me/account (soft delete + 30 gün + is_active=false)
- Frontend (Consumer Panel): AccountProfile + PrivacyCenter yeni v1 endpointlerine bağlı
- **Portal yeniden tasarımı (EU uyumlu):**
  - Turuncu zemin + üst yatay menü + sol alt menü
  - Bireysel/Ticari menü farkları uygulandı
  - TR/DE/FR menü dili toggle
- Dealer portal ek sayfalar: Şirket Profili + Gizlilik Merkezi
- **Admin kategori modalı:**
  - Hiyerarşi adı → Kategori
  - Seviye bazlı sütunlar: her seviyede çoklu kategori kartı + Tamam ile bir sonraki seviyeye geçiş
  - Alt seviye kolonları, seçilen kategoriye göre açılıyor
  - Seviye Tamam: ad/slug doluysa tüm kartları tamamlar ve sonraki seviyeyi açar
  - Düzenle: kilitlenen seviye/öğe yeniden açılabilir
  - Akış: her adımda "Devam" (Next), son adımda "Kaydet"
- **Admin kategori parametre alanları:**
  - Parametre alanlarında seçenekleri tek tek ekleme/çıkarma arayüzü
  - Parametre listesinde seçenek ve zorunluluk özetleri
- **Admin kategori sihirbazı P0 düzeltmeleri (2026-02-22):**
  - Tamam → PATCH (server response authoritative)
  - Next gating + tooltip: “Önce bu adımı tamamlayın.”
  - Kategori → Çekirdek Alanlar → Parametre Alanları sırası enforce
- **Admin kategori sihirbazı Edit Mode state sync (2026-02-23):**
  - wizard_progress backend tek kaynak; save/unlock sonrası UI store güncelleniyor
  - Edit unlock başarısızsa snapshot rollback
  - Downstream dirty adımlar UI’da görünür
- **Admin Dirty CTA + Analytics (2026-02-23):**
  - “Sıradaki eksik adımı tamamla” CTA + ilk dirty tab yönlendirmesi
  - admin_dirty_cta_clicked / admin_dirty_first_step_opened payload (category_id, step_id, admin_user_id, wizard_state)
- **Son Seçiminiz (2026-02-23):**
  - user_recent_categories tablosu + upsert + GET endpoint
  - Drill-down ekranında kategori adı + breadcrumb + modül + ülke kartı
  - Vehicle modülünde /account/create/vehicle-wizard yönlendirmesi
- **İlan Ver (Emlak) yeni akış:**
  - /ilan-ver/kategori-secimi sütunlu drill-down + breadcrumb + arama kutusu
  - /ilan-ver/detaylar placeholder (detay formu daha sonra)
  - /api/categories/children + /api/categories/search endpointleri

- **İlan ver sihirbazı (create listing):**
  - Başlıklar/boş durumlar/section alanları için data-testid eklendi
  - Dropzone + cover etiketleri test-id ile tamamlandı
- **Çekirdek Alanlar fiyat tipi (2026-02-23):**
  - price_type (FIXED/HOURLY) + hourly_rate desteği (backend + frontend)
  - Fiyat/Saatlik Ücret toggle + tek input swap + doğrulama mesajları
  - Public detay ve aramada “{amount} {currency}” / “{rate} {currency} / saat”
  - Fiyat filtresi yalnız FIXED ilanlara uygulanıyor
- **Listing wizard altyapı stabilizasyonu (2026-02-23):**
  - /api/catalog/schema draft schema erişimi açıldı (wizard blokları kalktı)
  - /api/v2/vehicle/makes + models SQL fallback eklendi
- **Premium otomobil ilan sihirbazı P0 (2026-02-23):**
  - Model grid + arama + seçim (geri/ileri persist)
  - Yıl dropdown (2010–2026) + opsiyonel Versiyon/Donanım metin alanı
  - Make/Model/Year Next autosave + “Kaydedildi” toast + step değişiminde scroll-to-top (preview hariç)
  - Autosave analytics eventleri: wizard_step_autosave_success / wizard_step_autosave_error
  - Yıl adımı model seçilmeden kilitli + state sync
  - Oto çekirdek alanları: km, yakıt, vites, çekiş, kasa, motor cc/hp, hasar, takas, konum + fiyat tipi entegrasyonu
  - Özellikler/Medya: min 3 foto + kapak + sıralama, review’da galeri özeti
  - Önizleme: marka/model/yıl, fiyat tipi, motor, konum, özellik özetleri
  - Draft save PATCH + create draft make/model opsiyonel
  - Şema yükleme 409 notice + kullanıcıya bilgi mesajı
  - DB client_encoding UTF8 (TR karakterler)
  - App.js VehicleSegmentPage import fix
- **Kategori import/export (2026-02-23):**
  - CSV + XLSX export (module + country filtreleri)
  - Import dry-run + apply, slug ile eşleştirme, wizard_progress taşıma
  - Validasyon: zorunlu alanlar, duplicate slug, cycle, satır hata raporu
  - Audit log (import.dry_run, import.apply)
  - Örnek dosyalar: backend/tests/fixtures/categories-import-sample.(csv/xlsx)
- **Kategori import/export P0.1 (2026-02-23):**
  - Örnek CSV/XLSX indir endpoint’leri (module/country filtreli)
  - schema_version = v1 kolonlu şablon + root/child örnek satır
- **Genel “İlan Ver” drill-down (P1 başlangıcı, 2026-02-23):**
  - Modül seçimi + L1..Ln kategori drill-down + arama
  - Son Seçiminiz kartı (breadcrumb + module + ülke)
  - Vehicle modülü → /account/create/vehicle-wizard, diğerleri → /account/create/listing-wizard
  - Analytics event’leri: step_select_module, step_select_category_Ln
  - /api/analytics/events endpointi audit log ile kayıt
- Preview/Prod DB fail-fast: CONFIG_MISSING hatası + localhost yasak + DB_SSL_MODE=require
- .env override kapatıldı (server.py, core/config.py, app/database.py)
- **P0 Sertleştirmeler:**
  - /api/health/db → migration_state gate + 60sn cache + last_migration_check_at
  - /api/health → config_state + last_migration_check_at + ops_attention + last_db_error
  - Register honeypot (company_website) + server-side reject + audit log (register_honeypot_hit)
  - GDPR export completion notification (in-app, warning) + audit trail
- **Mongo temizliği (moderasyon):**
  - Moderation queue/count/detail SQL’e taşındı
  - Approve/Reject/Needs‑revision SQL akışı + ModerationAction + audit log
  - Geçici ETL endpointi kaldırıldı (Mongo runtime cleanup başlangıcı)
- **Moderation Freeze UI (2026-02-24):**
  - Admin System Settings toggle kartı metinleri + açıklama notu güncellendi
  - Moderation Queue + detay + aksiyon diyaloglarında banner gösterimi
  - Approve/Reject/Needs Revision aksiyonları disable + tooltip
- **Local Infra:**
  - PostgreSQL kuruldu, app_local DB oluşturuldu
  - Alembic upgrade heads PASS
  - Stripe CLI kuruldu (auth/test key invalid → idempotency BLOCKED)
- **Preview E2E:**
  - Admin login + Moderation Queue PASS
  - Consumer/Dealer login + profil endpointleri PASS
- **DB 520 Stabilizasyonu (2026-02-23):**
  - SQLAlchemy pool konfigürasyonu için runtime “effective config” logu + pool lifecycle logları (INFO + debug flag)
  - get_db / get_sql_session: rollback + deterministic close
  - CorrelationIdMiddleware aktif + DB error loglarında request_id
  - Load test: Faz‑1 1000 sequential login+me, Faz‑2 10 paralel toplam 1000 istek → 0 adet 520 (p95 ~2924ms / 5074ms)
  - /app/load_test.py eklendi
  - P1 smoke: Auth + Vehicle wizard + Admin categories edit modal PASS
- **Wizard Autosave Status Badge (2026-02-23):**
  - Badge metni: “Kaydedildi • HH:MM” (backend updated_at)
  - Hata: “Kaydedilemedi”
- **System Health Mini-Badge (2026-02-23):**
  - /api/admin/system/health-summary endpointi + 60sn cache
  - Admin header badge (DB status, last check, 5dk error rate)
- **System Health Detail Panel (2026-02-23):**
  - /api/admin/system/health-detail endpointi + 60sn cache
  - 24s hata oranı sparkline + DB latency avg/p95 + son ETL zamanı
  - Slow queries (24s) rozeti, threshold >800ms
  - Endpoint bazlı slow query kırılımı (/api/search, /api/listings, /api/admin/*)
- **CDN Metrics Adapter (Cloudflare) (2026-02-23):**
  - Health panel CDN hit ratio, origin fetch, warm/cold p95 (feature-flag)
  - Country breakdown + sparkline + canary status + cf_ids_present/source
- **Cloudflare Config Admin UI (2026-02-23):**
  - System Settings kartı + masked inputs + canary test
  - CONFIG_ENCRYPTION_KEY health flag + save guard + failure reason logs
  - Tek durum mesajı + kullanıcı dostu canary + teknik detay tooltip
- **Phase A Ops Inject Closeout (2026-02-23):** env/secret inject + canary OK + kanıt: `/app/docs/ADMIN_V1_PHASE_A_EVIDENCE.md`
- **Phase B RBAC Hard Lock Kickoff (2026-02-23):** deny-by-default allowlist + admin UI guard + docs: `/app/docs/RBAC_MATRIX.md`, `/app/docs/RBAC_ENDPOINT_MAP.md`, `/app/docs/RBAC_NEGATIVE_TESTS.md`
- **Data Layer Cutover Kickoff (Mongo Tasfiye) (2026-02-23):**
  - Mongo envanteri + dönüşüm haritası + şema gap raporu
  - P0 admin chain SQL: system-settings + admin invite (520 → 0)
  - Dokümanlar: `/app/docs/MONGO_INVENTORY.md`, `/app/docs/MONGO_TO_SQL_MAP.md`, `/app/docs/SQL_SCHEMA_GAP_REPORT.md`, `/app/docs/SQL_SCHEMA_COMPLETION_PACKAGE.md`, `/app/docs/MONGO_SQL_MIGRATION_PLAN.md`, `/app/docs/MONGO_SQL_MIGRATION_EVIDENCE.md`
- **Dependency Resolver Fix (2026-02-23):**
  - google-api-core hard pin kaldırıldı, dar aralıkla sabitlendi (>=2.28.1,<2.31.0)
- **Admin Kategori Manuel Yönetimi (2026-02-23):**
  - Modül seçimi + parent validation + alt tip metadata
- **İlan Ver Kategori Fallback (2026-02-23):**
  - Veri yoksa güvenli fallback + CTA
- **Search Postgres Cutover (2026-02-23):**
  - SEARCH_SQL_ROLLOUT %50 → %100
  - Seed demo data (5000 ilan) + ETL tekrar çalıştırıldı
  - Parity + benchmark raporları güncellendi
  - Pending Ops 24h monitoring: /app/memory/SEARCH_24H_MONITORING_REPORT.md
  - Raporlar: /app/memory/SEARCH_PARITY_REPORT.md, /app/memory/SEARCH_PARITY_RAW.md, /app/memory/SEARCH_BENCHMARK_REPORT.md, /app/memory/SEARCH_SLOW_QUERIES.md
- **Moderation Items Migration (2026-02-23):**
  - moderation_items SQL tablosu + model + Pydantic schema
  - p38 migration uygulandı
  - ETL: scripts/migrate_moderation_items_from_mongo.py (reason sanitize + status normalize + UTC)
  - Parity raporu: /app/memory/MODERATION_PARITY_REPORT.md (sample 50)
  - ETL (admin ops) çalıştırıldı; Mongo moderation_queue bulunamadı (count=0)
  - Admin moderation queue/count SQL artık moderation_items üzerinden
  - Listing submit/request-publish sırasında moderation_item upsert
  - Cutover plan: /app/memory/MODERATION_CUTOVER_PLAN.md

## Kanıtlar
- /app/docs/LOCAL_DB_READY_EVIDENCE.md
- /app/docs/MIGRATION_DRIFT_SIMULATION_EVIDENCE.md
- /app/docs/STRIPE_CLI_INSTALL_EVIDENCE.md
- /app/docs/STRIPE_IDEMPOTENCY_LOCAL_EVIDENCE.md
- /app/docs/STRIPE_IDEMPOTENCY_EVIDENCE.md
- /app/docs/P0_1_SECURITY_HARDENING_CLOSED.md
- /app/docs/LOGIN_RATE_LIMIT_EVIDENCE.md
- /app/docs/TWO_FACTOR_CHALLENGE_EVIDENCE.md
- /app/docs/TWOFA_BACKUP_CODE_EVIDENCE.md
- /app/docs/PUBLIC_SEARCH_MONITORING_REPORT.md
- /app/docs/RBAC_COVERAGE_GATE.md
- /app/docs/RBAC_CI_PR_COMMENT_DECISION.md
- /app/docs/MODERATION_FREEZE_WINDOW_PLAN.md
- /app/docs/ADMIN_INVITE_PREVIEW_SPEC.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_EVIDENCE.md
- /app/docs/GDPR_EXPORT_SOFT_DELETE_E2E.md
- /app/docs/AUTH_SECURITY_STRESS_EVIDENCE.md
- /app/docs/AUDIT_CHAIN_PARITY_EVIDENCE.md
- /app/docs/HEALTH_OPS_VISIBILITY_SPEC.md
- /app/docs/PROFILE_ENDPOINT_FIX_EVIDENCE.md
- /app/docs/PREVIEW_DB_FIX_EVIDENCE.md
- /app/docs/PREVIEW_MIGRATION_EVIDENCE.md
- /app/docs/HEALTH_MIGRATION_GATE_SPEC.md
- /app/docs/HEALTH_MIGRATION_GATE_EVIDENCE.md
- /app/docs/HEALTH_MIGRATION_GATE_PREVIEW_EVIDENCE.md
- /app/docs/PREVIEW_MIGRATION_PARITY_EVIDENCE.md
- /app/docs/SPRINT1_PREVIEW_API_EVIDENCE.md
- /app/docs/SPRINT1_PREVIEW_E2E_EVIDENCE.md
- /app/docs/SPRINT_PREVIEW_ADMIN_E2E_EVIDENCE.md
- /app/docs/SPRINT1_CLOSEOUT.md
- /app/docs/ADMIN_V1_PHASE_A_EVIDENCE.md
- /app/docs/MONGO_INVENTORY.md
- /app/docs/MONGO_TO_SQL_MAP.md
- /app/docs/SQL_SCHEMA_GAP_REPORT.md
- /app/docs/SQL_SCHEMA_COMPLETION_PACKAGE.md
- /app/docs/MONGO_SQL_MIGRATION_PLAN.md
- /app/docs/MONGO_SQL_MIGRATION_EVIDENCE.md
- /app/docs/FINAL_520_ZERO_REPORT.md
- /app/docs/DATA_LAYER_CUTOVER_CLOSED.md
- /app/memory/MONGO_INVENTORY.md
- /app/docs/RBAC_MATRIX.md
- /app/docs/RBAC_ENDPOINT_MAP.md
- /app/docs/RBAC_NEGATIVE_TESTS.md
- /app/docs/REGISTER_ANTIBOT_HONEYPOT_SPEC.md
- /app/docs/REGISTER_ANTIBOT_HONEYPOT_EVIDENCE.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_SPEC.md
- /app/docs/GDPR_EXPORT_NOTIFICATION_EVIDENCE.md
- /app/docs/GDPR_EXPORT_SOFT_DELETE_E2E.md
- /app/docs/OPS_ESCALATION_TICKET.md
- /app/docs/PREVIEW_UNBLOCK_TRACKER.md
- /app/docs/LOCAL_PREVIEW_SIMULATION_EVIDENCE.md
- /app/docs/PREVIEW_ACTIVATION_RUNBOOK.md
- /app/memory/MONGO_TO_POSTGRES_MIGRATION_PLAN.md
- /app/memory/SEARCH_PARITY_REPORT.md
- /app/memory/SEARCH_PARITY_RAW.md
- /app/memory/SEARCH_BENCHMARK_REPORT.md
- /app/memory/SEARCH_SLOW_QUERIES.md
- /app/memory/SEARCH_EXPLAIN_ANALYZE_RAW.md
- /app/memory/SEARCH_CUTOVER_PLAN.md
- /app/memory/SEARCH_24H_MONITORING_REPORT.md
- /app/memory/MODERATION_PARITY_REPORT.md
- /app/memory/MODERATION_CUTOVER_PLAN.md
- /app/memory/MONGO_DEPENDENCY_REPORT.md
- /app/memory/ADR.md
- /app/memory/LISTING_ENTRY_FLOW_ACCEPTANCE_CRITERIA.md
- /app/memory/ROADMAP.md
- /app/memory/CDN_24H_REPORT.md
- /app/memory/UX_THEME_PHASE_PREP.md

## Son Değişiklikler (2026-02-24)
- P0.1 kapanış paketleri hazırlandı: P0_1_SECURITY_HARDENING_CLOSED.md + backup code + log-based 24h raporu.
- 2FA backup code tek-kullanım kanıtlandı (curl + UI).
- Public search log-based 24h window CLOSED olarak raporlandı.
- Moderation freeze window planı kilitlendi.
- RBAC CI PR comment workflow güncellendi + karar dokümante edildi.
- Moderation Freeze UI: Admin System Settings toggle metni güncellendi + Moderation Queue banner/tooltip/disable davranışı tamamlandı.
- Moderation Freeze reason alanı + audit event (ENABLED/DISABLED) + banner reason gösterimi eklendi.
- Moderation Freeze evidence + closeout: MODERATION_FREEZE_EVIDENCE.md, MODERATION_FREEZE_CLOSED.md.
- Privacy Center Export History (gdpr_exports tablosu + 30 gün retention + /account/privacy Export Geçmişi tabı) tamamlandı.
- FAZ-UH1 dokümantasyonu tamamlandı: /architecture/ui/* (purpose, data sources, IA v2, wireframe, backlog, tokens).
- Consumer Dashboard V1 aksiyon odaklı yeniden kuruldu (KPI row, primary CTA, listing snapshot, favoriler/saved search, status banner).
- /account/security route eklendi + sol menü IA V2 güncellendi.
- UH1 closeout + regression checklist + Quick Preview spec + P2 dependency dokümanları yayınlandı.
- FAZ-ADMIN-FINAL Sprint1 dependency map + gap list + implementation order + ticket taslağı oluşturuldu.
- AF Sprint1 migration impact analizi tamamlandı (/architecture/admin/AF_SPRINT1_MIGRATION_IMPACT.md).
- Migration dry-run katmanı eklendi (scripts/migration_dry_run.py + spec + runbook gate + PR checkbox + CI job).

## Blokajlar / Riskler
- Cloudflare config kaydı için CONFIG_ENCRYPTION_KEY gerekli (preview env sağlandı; eksikse kaydetme bloklanır)

## Öncelikli Backlog
### P0 (Hemen)
- ✅ Data Layer Cutover (Mongo Tasfiye): Mongo 0-iz + 520=0 + Dealer/Consumer E2E tamamlandı
- ✅ Admin V1 Phase B (RBAC Final Freeze): MATRIX/ENDPOINT MAP FREEZE v1 + negatif test kanıtları + portal guard doğrulaması
- ✅ Preview GDPR export + soft delete E2E kanıtları + audit doğrulaması
- ✅ Honeypot 400 + register_honeypot_hit audit doğrulaması (preview)
- ✅ Stripe idempotency testi (Checkout flow)

### P0.1 (Güvenlik Doğrulama)
- ✅ Login rate limit tetikleme testi (preview)
- ✅ 2FA challenge (enable → wrong OTP → success) kanıtı (preview)
- ✅ 2FA backup code tek kullanımlık testi (preview)
- ✅ Soft delete → login blocked testi (preview)
- ✅ GDPR export sonrası notification banner UI doğrulaması

### P1 (Aktif)
- ✅ Public Search 24h monitoring: log-based 24h CLOSED
- ✅ Moderation migration: SQL parity report + freeze window plan kilitlendi
- 🔵 Admin Operasyonel Finalizasyon (FAZ-ADMIN-FINAL) başlatıldı

### P1 (Sprint‑1 closeout)
- Sprint‑1 E2E kanıt paketi

### P1.5 / P2 (Enhancement)
- ✅ Privacy Center export geçmişi (gdpr_exports tablosu + UI) → /app/docs/PRIVACY_EXPORT_HISTORY_SPEC.md
- 🔵 Quick Preview Modal (UH1-E1) — /architecture/ui/LISTING_QUICK_PREVIEW_SPEC.md

### P2
- Kayıtlı Arama/Alert (P2 backlog, P1 kapsamına girmez)
- P2 Saved Search Integration → /architecture/ui/P2_SAVED_SEARCH_INTEGRATION.md
- P2 Quota API Binding → /architecture/ui/P2_QUOTA_API_BINDING.md
- VIES VAT doğrulama (API)
- GDPR CSV export
- Public search + admin listings Mongo bağımlılıklarının SQL’e taşınması
- Verification token cleanup job
