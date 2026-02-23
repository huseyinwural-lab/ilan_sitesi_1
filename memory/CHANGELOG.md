# CHANGELOG

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
