# ROADMAP

**Son güncelleme:** 2026-02-26

Bu dosya faz bazlı backlog özetini içerir. Detaylı iş listeleri PRD’de tutulur.

## Faz Durumu

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
- Watermark & Image Processing — BACKLOG
- Transactions Log — BACKLOG
- Attribute Manager — BACKLOG
- Minimal Moderation — BACKLOG
- Search final polish (facet UI + suggest) — BACKLOG

---

## P2 Backlog
- Kampanya timeline
- Doping sistemi
- Public campaign/search UI
