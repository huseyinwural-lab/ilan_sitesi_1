# ROADMAP

**Son güncelleme:** 2026-02-26

Bu dosya faz bazlı backlog özetini içerir. Detaylı iş listeleri PRD’de tutulur.

## Faz Durumu

### Admin Phase
- **CLOSED** ✅
- Launch eşiği modülleri tamamlandı: Watermark, Transactions Log, Attribute Manager (Search uyum), Minimal Moderation, Search final polish.
- **Admin Freeze aktif:** Yeni admin feature alınmaz. Sadece bugfix / güvenlik patch.

### P0 — Kategori Yönetimi Düzeltmesi (BLOCKER)
- **DONE** ✅ (2026-02-26)
- Kapsam: `other` modülü, manuel sıra, scope unique constraint, vehicle segment-link akışı, real_estate/other regresyonu
- Kanıtlar:
  - `/app/test_reports/iteration_20.json`
  - `/app/docs/CATEGORY_ORDER_MIGRATION_REPORT.md`
- Not: Kullanıcı kararı gereği Dealer Dashboard’a dönmeden önce Category hardening/test turu tamamlandı.

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
- Dealer Dashboard + Manuel Kontrol Sistemi v1 — **IN PROGRESS (PAUSED)** 🟡
  - Backend foundation hazır (config modelleri + API)
  - Öncelik sırası gereği kategori P0 sonrası yeniden ele alınacak

---

## P2 Backlog
- Kampanya timeline
- Doping sistemi
- Public campaign/search UI
