# CHANGELOG

## 2026-02-27 — P64 Publish Hardening P0

**Kapsam**
- Publish endpointlerinde `config_version` zorunlu:
  - Yeni endpoint: `/api/admin/ui/configs/{config_type}/publish`
  - Legacy endpoint: `/api/admin/ui/configs/{config_type}/publish/{config_id}` (deprecated)
- Hata kontratı:
  - `400 MISSING_CONFIG_VERSION`
  - `409 CONFIG_VERSION_CONFLICT` (+ `current_version`, `your_version`, `last_published_by`, `last_published_at`)
  - `409 PUBLISH_LOCKED`
  - `400 MISSING_ROLLBACK_REASON`
- Publish lock (kısa süreli) eklendi.
- Rollback reason zorunlu yapıldı, audit metadata’ya yazım eklendi.
- Dashboard publish dialogu görsel diff panelleriyle güçlendirildi (Önceki/Yeni grid, highlight).
- UI conflict modal eklendi (`Sayfayı Yenile`, `Diff Gör`).
- Rollback UX: `Son Snapshot’a Dön` hızlı butonu + reason zorunlu input.

**Kanıt/Test**
- Evidence: `/app/docs/UI_PUBLISH_HARDENING_P0_EVIDENCE.md`
- Testing agent: `/app/test_reports/iteration_30.json` (PASS)
- Pytest: `37 passed` (p61+p62+p62_extended+p63+p64)

## 2026-02-26 — P63 Logo Upload Contract Stabilization

**Kapsam**
- Kurumsal header logo upload API kontratı standardize edildi: `detail.code/message/details`.
- Error code’lar: `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`, `INVALID_ASPECT_RATIO`, `INVALID_FILE_CONTENT`, `STORAGE_PIPELINE_ERROR`.
- Frontend `CorporateHeaderDesigner` içinde inline error banner eklendi (özet + beklenen/gelen + kod).
- Upload sonrası preview URL cache-bust eklendi (`?v=timestamp`), success toast + güncel preview akışı doğrulandı.
- Storage hattı görünürlüğü: upload success response içine `storage_health` ve yeni `GET /api/admin/ui/logo-assets/health` endpointi.
- RBAC/scope doğrulaması: dealer 403, `scope=system + scope_id` normalize davranışı doğrulandı.

**Kanıt/Test**
- Testing agent raporu: `/app/test_reports/iteration_29.json` (PASS)
- Evidence: `/app/docs/LOGO_UPLOAD_P0_STABILIZATION_EVIDENCE.md`
- Pytest: `backend/tests/test_p63_logo_upload_contract.py`, `backend/tests/test_p60_corporate_header_logo.py`

## 2026-02-26 — P62 Dealer Dashboard V2 P1 Frontend Integration

**Kapsam**
- Corporate Dashboard V2 admin editörü eklendi: 12 kolon grid + dnd-kit reorder + widget palette (KPI/Grafik/Liste/Paket Özeti/Doping Özeti).
- Guardrail UI senkronizasyonu: KPI yoksa publish disabled, max 12 widget limiti; draft autosave aktif.
- Draft→Preview→Publish akışı: diff ekranı (eklenen/kaldırılan/taşınan), zorunlu onay modalı, publish endpoint confirm ile çağrılıyor.
- Rollback akışı: snapshot/versiyon seçip geri alma; dashboard ve individual header için aktif.
- Individual Header editörü row-based DnD + visible toggle + logo fallback ile yenilendi.
- Dealer canlı dashboard sayfası config-driven widget render yapacak şekilde güncellendi.

**Backend Workflow Genişletmeleri**
- Yeni endpointler: `/api/admin/ui/configs/{config_type}/diff`, `/publish`, `/rollback`.
- Publish/Rollback sırasında audit log yazımı eklendi (`ui_config_publish`, `ui_config_rollback`).

**Kanıt/Test**
- Testing agent raporu: `/app/test_reports/iteration_28.json` (Backend + Frontend PASS)
- Self-test: `pytest -q backend/tests/test_p61_dashboard_backend.py backend/tests/test_p62_ui_publish_workflow.py` → `13 passed`
- Evidence dokümanı: `/app/docs/DEALER_DASHBOARD_V2_FRONTEND_EVIDENCE.md`

## 2026-02-26 — P61 Dealer Dashboard V2 P0 Backend-Only Stabilization

**Kapsam**
- Alembic: `p61_ui_dashboard_cfg` migration ile `ui_configs` tablosuna `layout/widgets` JSONB kolonları eklendi.
- Backend contract güncellemesi: `POST /api/admin/ui/configs/dashboard`, publish akışı ve `GET /api/ui/dashboard` artık layout/widgets alanlarını native taşır.
- Guardrail enforce (backend): min 1 KPI, max 12 widget, duplicate `widget_id` ve layout-widget eşleşme doğrulaması.
- Migration güvence testi: upgrade → downgrade (`p60_ui_logo_assets`) → re-upgrade (`heads`) başarılı.
- Test raporu: `/app/test_reports/iteration_27.json` (PASS, backend 10/10).

## 2026-02-23 — Data Layer Cutover Kickoff (Mongo Tasfiye)

**Kapsam**
- Mongo envanteri + dönüşüm haritası + şema gap raporu
- P0 admin chain SQL: system-settings + admin invites (520 → 0)
- Dokümanlar: MONGO_INVENTORY, MONGO_TO_SQL_MAP, SQL_SCHEMA_GAP_REPORT, SQL_SCHEMA_COMPLETION_PACKAGE, MONGO_SQL_MIGRATION_PLAN, MONGO_SQL_MIGRATION_EVIDENCE

## 2026-02-23 — Phase B Kickoff (RBAC Hard Lock)

**Kapsam**
- Deny-by-default RBAC middleware + allowlist
- Admin endpoint policy haritası (RBAC_ENDPOINT_MAP.md)
- RBAC matrisi ve negatif test listesi (RBAC_MATRIX.md / RBAC_NEGATIVE_TESTS.md)
- Admin UI route guard (AdminLayout + shared adminRbac)

## 2026-02-23 — Admin V1 Phase A Closeout (Cloudflare Ops Inject)

**Kapsam**
- Env/secret inject + backend restart doğrulandı
- /api/admin/system/health-detail canary_status=OK
- Admin UI canary OK (screenshot: `/app/screenshots/cloudflare-card-final-state.jpeg`)
- Kanıt: `/app/docs/ADMIN_V1_PHASE_A_EVIDENCE.md`

## 2026-02-23 — CDN Metrics + Admin Kategori Manuel Yönetimi

**Kapsam**
- Cloudflare Metrics Adapter (feature-flag) + Health panel CDN göstergeleri
- CDN country breakdown + sparkline + canary status + cf_ids_present/source
- Admin System Settings: Cloudflare config kartı + masked input + canary
- CONFIG_ENCRYPTION_KEY health flag + save guard + error reason logs
- UX guard: tek durum satırı + canary inline detay + disable tooltip
- Admin kategori CRUD: modül seçimi + alt tip metadata + parent validation
- İlan ver kategori fallback mesajı + güvenli CTA
- UX & Theme Phase prep dokümanları (envanter + risk listesi)

## 2026-02-23 — Moderation ETL + Mongo Runtime Cleanup

**Kapsam**
- Moderation ETL çalıştırıldı (preview); parity raporu güncellendi, Mongo moderation_queue bulunamadı (0/0)
- Geçici ETL endpointi kaldırıldı; runtime tek DB (Postgres) teyidi
- Single DB Architecture Confirmed

## 2026-02-23 — P0 DB 520 Stabilizasyonu Closeout

**Kapsam**
- Pool effective config doğrulandı: pool_size=5, max_overflow=5, pool_timeout=30, pool_recycle=1800, pool_pre_ping=true
- Connection lifecycle logları (connect/checkout/checkin/invalidate) + CorrelationIdMiddleware
- get_db/get_sql_session rollback + deterministic close
- Load test sonuçları:
  - Faz-1: 1000 sequential login+me, 0×520, p95=2923.81ms
  - Faz-2: 10 paralel kullanıcı, toplam 1000 istek, 0×520, p95=5074.31ms

**Not**
- Stabilizasyon başarı kriterleri sağlandı.

## 2026-02-23 — P1 Search Migration Execution (Preview)

**Kapsam**
- Alembic p36 migration uygulandı (listings_search + full-text/faceted index seti)
- Mongo → SQL ETL çalıştırıldı (preview: 0 kayıt)
- Parity raporu: `/app/memory/SEARCH_PARITY_REPORT.md`
- Benchmark raporu: `/app/memory/SEARCH_BENCHMARK_REPORT.md`
- EXPLAIN ANALYZE ham çıktı: `/app/memory/SEARCH_EXPLAIN_ANALYZE_RAW.md`
- Feature flag: SEARCH_SQL_ROLLOUT (0.1 → 0.5 → 1.0)

**Performans Notu**
- Cold p50/p95: ~292.82 / 308.19 ms
- Warm p50/p95: ~145.49 / 147.9 ms


## 2026-02-23 — Search Postgres Cutover (Pending Ops 24h Monitoring)

**Kapsam**
- SEARCH_SQL_ROLLOUT %50 → %100 (preview)
- Seed demo data: 5000 ilan (multi kategori/modül)
- ETL tekrar çalıştırıldı (mongo_total=5000)
- Parity raporu güncellendi: `/app/memory/SEARCH_PARITY_REPORT.md`
- Benchmark raporu güncellendi (p50/p95/max): `/app/memory/SEARCH_BENCHMARK_REPORT.md`
- Slow query listesi: `/app/memory/SEARCH_SLOW_QUERIES.md`
- Search UI API prefix düzeltmesi (SearchPage /api/api/ → /api/)
- Rollback hazır, kullanılmadı
- 24h monitoring owner: Ops/Owner
- 24h monitoring raporu: `/app/memory/SEARCH_24H_MONITORING_REPORT.md`

## 2026-02-23 — Admin System Health Detail Panel

**Kapsam**
- /api/admin/system/health-detail endpointi (24s hata buckets, latency avg/p95, son ETL)
- Admin header panel: sparkline + metrik kartları
- Slow queries (24s) rozeti + threshold >800ms
- Endpoint bazlı slow query kırılımı (/api/search, /api/listings, /api/admin/*)

## 2026-02-23 — Moderation Migration Kickoff

**Kapsam**
- moderation_queue schema + p37 migration
- ETL script + parity raporu: `/app/memory/MODERATION_PARITY_REPORT.md`
- Cutover plan: `/app/memory/MODERATION_CUTOVER_PLAN.md`
- Not: Mongo moderation koleksiyonları bulunamadı (0/0 parity)

## 2026-02-23 — P0 Edit Mode State Sync Closeout

**Kapsam**
- Admin Category Wizard “Edit Mode” state senkronizasyonu (backend wizard_progress tek kaynak)
- Save sonrası downstream dirty adımların UI’da görünmesi
- Başarısız save/unlock için UI rollback

**Kanıt Referansları**
- Repro/analiz notu: `/app/memory/EDIT_MODE_SYNC_NOTES.md`
- Playwright senaryosu: admin login → edit unlock → dirty CTA görünür → CTA tıklandı
- Screenshot seti:
  - `/app/screenshots/admin-dirty-cta.png`
  - `/app/screenshots/admin-dirty-cta-after.png`
  - `/app/screenshots/admin-save-rollback.png`
  - `/app/screenshots/admin-multi-save.png`

**Regression Checklist**
- [x] Save rollback (Playwright: `/app/screenshots/admin-save-rollback.png`)
- [x] Multi-save ardışık deneme (Playwright: `/app/screenshots/admin-multi-save.png`)
- [x] Dirty zinciri görünürlüğü (Playwright: `/app/screenshots/admin-dirty-cta.png`)

## 2026-02-23 — P1 Closeout

**Kapsam**
- Recent category (user_recent_categories + upsert + GET)
- “Son Seçiminiz” kartı (breadcrumb + module + ülke)
- Dirty CTA + admin analytics
- Vehicle wizard Make/Model/Year + core + features/media + preview/publish

**Kanıt Referansları**
- Recent card: `/app/screenshots/recent-card.png`
- Dirty CTA: `/app/screenshots/admin-dirty-cta.png`
- Vehicle wizard review/publish:
  - `/app/screenshots/vehicle-wizard-review.png`
  - `/app/screenshots/vehicle-wizard-published.png`

**Not**
- E2E script trade_in dropdown — test script issue (uygulama bug değil)

## 2026-02-23 — P1.1 Wizard UX Mini İyileştirme

**Kapsam**
- Autosave toast (Kaydedildi, 2–3 sn)
- Step mount scroll-to-top (review hariç)
- Inline error + first invalid scroll
- Autosave status badge (Kaydedildi • HH:MM / Kaydedilemedi)
- Analytics: wizard_step_autosave_success / wizard_step_autosave_error / wizard_autosave_badge_rendered

**Test Durumu (Pending)**
- Playwright blocked due to 520 DB issue (pending re-run)

## 2026-02-23 — Kategori Import/Export P0 Closeout

**Kapsam**
- CSV + XLSX export (module + country filtreli)
- Import dry-run + apply (slug eşleştirme), translations + wizard_progress taşıma
- Validasyon: zorunlu alanlar, duplicate slug, cycle tespiti, satır bazlı hata raporu
- Yetki: super_admin + country_admin, audit log (import.dry_run, import.apply)

**Endpoint’ler**
- `GET /api/admin/categories/import-export/export/csv`
- `GET /api/admin/categories/import-export/export/xlsx`
- `POST /api/admin/categories/import-export/import/dry-run`
- `POST /api/admin/categories/import-export/import/commit`
- `GET /api/admin/categories/import-export/sample/csv`
- `GET /api/admin/categories/import-export/sample/xlsx`

**UI Akışı**
- Admin → Kategoriler → Import/Export (Export / Import / Dry-run Sonucu tabları)

**Kanıt Referansları**
- **API curl komut seti:** `cat_import_export_smoke_20260223`
  - login: `POST /api/auth/login`
  - export: `GET /api/admin/categories/import-export/export/csv?module=vehicle&country=DE`
  - sample: `GET /api/admin/categories/import-export/sample/csv?module=vehicle&country=DE`
  - dry-run: `POST /api/admin/categories/import-export/import/dry-run?format=csv`
  - apply: `POST /api/admin/categories/import-export/import/commit?format=csv&dry_run_hash=...`
- **UI screenshot paketi:** `automation_output/20260223_063203`  
  - `admin-categories-export.png`  
  - `admin-categories-import-sample.png`
- **auto_frontend_testing_agent:** “User Category Selection Drill-Down & Sample Download UI Test — PASS” (2026-02-23)

**Done Checklist**
- [x] Export filtreli (module + country)
- [x] Import dry-run + apply
- [x] Slug match (update)
- [x] Translations + wizard_progress
- [x] Row-level error raporu
- [x] Yetki kontrolü (admin-only)
- [x] Audit log

## 2026-02-26 — Admin Kapanış Sprinti Tamamlama

### Yakında Temizliği + Dashboard Stabilizasyonu
- Menu Management UI kaldırıldı; API feature flag kapalıyken `403 feature_disabled`
- Category Import/Export CSV-only + dry-run zorunlu
- Dashboard summary endpoint konsolide edildi, KPI click-through eklendi
- Test kanıtı: `/app/test_reports/iteration_16.json`, `/app/test_reports/iteration_17.json`

### Final Paket (Tek Teslim)
- Watermark & Image Pipeline
- Transactions Log (read-only + filtre + CSV)
- Attribute Manager stabilizasyonu
- Minimal Moderation hardening (listing/message reports)
- Search suggest endpoint + TTL cache
- Test kanıtı: `/app/test_reports/iteration_18.json`

## 2026-02-26 — Admin Resmi Kapanış

- Admin fazı: **CLOSED**
- Admin Freeze: yeni admin feature yok, sadece bugfix/güvenlik patch
- Kapanış kanıt paketi: `/app/docs/ADMIN_CLOSURE_EVIDENCE_PACKAGE_2026-02-26.md`
- Public Phase strateji planı: `/app/memory/PUBLIC_PHASE_STRATEGIC_PLAN.md`

## 2026-02-26 — Dealer Dashboard + Manuel Kontrol Sistemi v1

- Bilgi mimarisi/route haritası tamamlandı (`/dealer/overview` ... `/dealer/settings`)
- Config modelleri eklendi: `dealer_nav_items`, `dealer_modules`
- Admin Kurumsal Menü Yönetimi: dnd-kit reorder + visible toggle + preview + audit
- Dealer layout config-driven render (header + sidebar)
- Dashboard tek summary endpoint + TTL cache + error contract
- Dealer KPI event tracking: `dealer_nav_click`, `dealer_widget_click`, `dealer_listing_create_start`, `dealer_contact_click`
- Final test: `/app/test_reports/iteration_19.json` PASS
- Evidence: `/app/docs/DEALER_DASHBOARD_V1_EVIDENCE.md`

## 2026-02-26 — CATEGORY P0 Stabilizasyon Revize (ADS-VEH-SEG-03)

- Vehicle segment akışı: serbest metin + master data zorunlu eşleşme
- API hata kontratları: `ORDER_INDEX_ALREADY_USED (400)`, `VEHICLE_SEGMENT_NOT_FOUND (400)`
- Yeni endpoint: `GET /api/admin/categories/order-index/preview` (canlı sıra çakışma önizleme)
- Vehicle segment country-unique kuralı aktif (aynı segment aynı ülkede tekil)
- Migration: `/app/backend/migrations/versions/p57_category_ordering_stabilization.py`
- Rapor: `/app/docs/CATEGORY_ORDER_MIGRATION_REPORT.md`
- Test: `/app/test_reports/iteration_21.json` PASS (backend 19/19)

## 2026-02-26 — CATEGORY P0 Resmi Kapanış

- ROADMAP statüsü `CLOSED` olarak güncellendi + `CATEGORY_MODULE_STABLE` internal milestone eklendi.
- Category freeze kararı işlendi (yalnızca bugfix).
- Swagger/OpenAPI response örnekleri doğrulandı (`ORDER_INDEX_ALREADY_USED`, `VEHICLE_SEGMENT_NOT_FOUND`).
- Kapanış regresyon raporu: `/app/test_reports/iteration_22.json` PASS.
- Sonraki faz aktif edildi: Dealer Dashboard P1 restart kapsam başlıkları roadmap’e işlendi.

## 2026-02-26 — Dealer Dashboard P1 Core + Category Bulk Operations

- Dealer portal config genişletildi: `header_row1_items`, `header_row1_fixed_blocks`, `header_row2_modules`, `header_row3_controls`
- DealerLayout 3 katmanlı header production-ready (row1 sabit+hızlı aksiyon, row2 modül sıralı chips, row3 mağaza filtresi + user dropdown)
- Admin Dealer Config: dnd-kit reorder persist akışı sertleştirildi (error handling + save feedback)
- Category list tri-state selection + bulk action bar + delete için çift doğrulama modalı (`ONAYLA`) eklendi
- Yeni endpoint: `POST /api/admin/categories/bulk-actions` (action + scope + ids/filter)
- Category list API filtreleri genişletildi: `country`, `module`, `active_flag`
- Test: `/app/test_reports/iteration_23.json` PASS (backend 22/22, frontend 100%)

## 2026-02-26 — Dealer P1 Iterasyon 2 (Undo + Draft Mode + Bulk Async)

- Yeni model/migration: `dealer_config_revisions`, `category_bulk_jobs` (`p58_dealer_draft_bulk_jobs`)
- Dealer Admin Config ekranı Draft Mode’a alındı:
  - Persist öncesi undo (revision stack)
  - Persist edilmemiş değişiklik uyarısı (navigation/beforeunload guard)
  - Draft save, publish, revisions list, rollback akışları
- Bulk Actions altyapısı async olacak şekilde genişletildi:
  - `<=1000` sync, `>1000` async queue
  - `POST /api/admin/categories/bulk-actions/jobs/{job_id}` polling
  - idempotency key + retry/backoff + lock TTL + telemetry log entries
- Test: `/app/test_reports/iteration_24.json` PASS (backend 10/10, frontend 10/10)
