# ROADMAP

**Son güncelleme:** 2026-02-27 (P64)

Bu dosya faz bazlı backlog özetini içerir. Detaylı iş listeleri PRD’de tutulur.

## Faz Durumu

### Admin Phase
- **CLOSED** ✅
- Launch eşiği modülleri tamamlandı: Watermark, Transactions Log, Attribute Manager (Search uyum), Minimal Moderation, Search final polish.
- **Admin Freeze aktif:** Yeni admin feature alınmaz. Sadece bugfix / güvenlik patch.

### P0 — Kategori Yönetimi Düzeltmesi (BLOCKER)
- **CLOSED** ✅ (2026-02-26)
- Kapsam: `other` modülü, manuel sıra, scope unique constraint, vehicle segment-link akışı, real_estate/other regresyonu
- Kanıtlar:
  - `/app/test_reports/iteration_20.json`
  - `/app/docs/CATEGORY_ORDER_MIGRATION_REPORT.md`
- Not: Kullanıcı kararı gereği Dealer Dashboard’a dönmeden önce Category hardening/test turu tamamlandı.
- Revize stabilizasyon: `ORDER_INDEX_ALREADY_USED` / `VEHICLE_SEGMENT_NOT_FOUND` error contractları + canlı sıra önizleme endpointi + vehicle segment country-unique kuralı.
- **Internal Milestone:** `CATEGORY_MODULE_STABLE`
- **Category Freeze aktif:** Bu modülde bundan sonra sadece bugfix.

### P0 — ListingWizard + VehicleSelector Stabilizasyonu
- **CLOSED** ✅
- Kanıt: `/app/docs/P0_VEHICLE_SELECTOR_FIX_EVIDENCE.md`

### P1 — Search Altyapısı (Meilisearch)
- **ACTIVE** 🔴
- Bu tur tamamlananlar:
  - Meilisearch config management (manual + history + activation gate)
  - P1.2 Listing→Index sync core (event hook + retry queue + bulk reindex + smoke endpoints)
  - External Meili aktivasyonu + canlı doğrulama (health/stage-smoke/reindex/event-sync)
  - P1.3 başlangıç: Meili tabanlı facet aggregation + dinamik sidebar veri akışı
- Kanıt: `/app/docs/P1_MEILI_CONFIG_HISTORY_EVIDENCE.md`
  - Ek kanıt: `/app/docs/P1_2_LISTING_INDEX_SYNC_EVIDENCE.md`

### P1 — Sıradaki (devam)
- Facet/dinamik sidebar UI polish + kategori bazlı facet genişletmesi
- Suggest/autocomplete endpoint
- URL/query state standardizasyonu + breadcrumb senkronu

### Admin Final Kilit (4 Modül)
- Yakında Temizliği — **DONE** ✅ (CSV-only import/export + Menu Management disabled)
- Dashboard Stabilizasyonu — **DONE** ✅ (tek summary endpoint + KPI click-through)
- Watermark & Image Processing — **DONE** ✅
- Transactions Log — **DONE** ✅
- Attribute Manager — **DONE** ✅
- Minimal Moderation — **DONE** ✅
- Search final polish (facet UI + suggest) — **DONE** ✅

### Sonraki Faz (Public Phase - P-UX) **ACTIVE** 🔴
- Suggest → sonuç → detay akışı optimizasyonu
- Facet UX sadeleştirme
- Listing detail conversion odaklı düzenleme (CTA / premium badge / güven öğeleri)
- Conversion funnel event tracking (suggest_open, search_submit, result_click, detail_view, contact_click)
- P1 hardening paralel: Suggest cache Redis planı, nightly DB↔Meili drift cron, admin health widget (index status)

### Public/Commercial Phase Durumu
- Dealer Dashboard + Manuel Kontrol Sistemi v1 — **IN PROGRESS (RESTARTED)** 🔴
  - Backend foundation + P1 core implementasyonu hazır (config render, 3 katman header, dnd persist)
  - Kategori P0 kapanışı sonrası yeniden başlatıldı ve ilk iterasyon PASS aldı (`/app/test_reports/iteration_23.json`)
  - **Yeni:** P0 backend stabilization tamamlandı (`p61_ui_dashboard_cfg`, dashboard guardrails, test PASS `/app/test_reports/iteration_27.json`)
  - **Yeni:** P1 frontend entegrasyon PASS (`/app/test_reports/iteration_28.json`) — corporate dashboard grid editor + individual header editor + diff/publish/rollback akışları canlı
  - **Yeni:** Logo upload P0 stabilizasyon PASS (`/app/test_reports/iteration_29.json`) — kontrat bazlı hata kodları, inline error banner, storage health, cache bust
  - **Yeni:** Publish Hardening P0 PASS (`/app/test_reports/iteration_30.json`) — config_version zorunluluğu (new+legacy), 409 conflict kontratı, publish lock, rollback reason zorunluluğu, görsel diff publish kontrolü

### Sıradaki Faz — Dealer Dashboard P1 (Restart)
- **ACTIVE** 🔴
- P1 çekirdek entegrasyon tamamlandı: Corporate Dashboard Grid DnD + Individual Header DnD + diff/publish/rollback
- Bu iterasyonda tamamlananlar:
  - Config-driven render finalizasyonu (header row1/row2/row3 + modules)
  - dnd-kit menü yönetimi kalıcı kaydetme
  - Header 1. satır sabit default set + manuel sıralama
  - 2. satır modül bazlı manuel sıralama
  - 3. satır mağaza filtresi + kullanıcı dropdown
  - Iterasyon 2: Undo paneli (persist öncesi), draft save/publish/rollback, revision listesi
  - Bulk 1000+ async job altyapısı (job queue + polling + idempotency + retry)
- Sonraki iterasyon:
  - Header mimari sadeleştirme: bireysel header editörü ve bireysel tema override kaldırma (feature_disabled/403)
  - Dealer header erişim güvenliği + publish snapshot sertleştirme
  - Widget şablon kütüphanesi (bu sprint dışı, V2 stabil sonrası UX hızlandırıcı)
  - Bulk job admin monitör ekranı (listeleme + retry butonu)

---

## P2 Backlog
- Kampanya timeline
- Doping sistemi
- Public campaign/search UI
