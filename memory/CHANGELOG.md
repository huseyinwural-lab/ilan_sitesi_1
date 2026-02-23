# CHANGELOG

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

## 2026-02-23 — P1 Recent Category + Dirty CTA + Vehicle Wizard

**Kapsam**
- user_recent_categories tablosu + upsert + GET endpoint
- “Son Seçiminiz” kartı (module + ülke + breadcrumb + tek tıkla devam)
- Dirty CTA (Sıradaki eksik adımı tamamla) + admin analytics eventleri
- Premium araç wizard akışı: Make/Model/Year gating + E2E publish

**Kanıt Referansları**
- Recent card: `/app/screenshots/recent-card.png`
- Dirty CTA: `/app/screenshots/admin-dirty-cta.png`
- Vehicle wizard review/publish:
  - `/app/screenshots/vehicle-wizard-review.png`
  - `/app/screenshots/vehicle-wizard-published.png`

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
