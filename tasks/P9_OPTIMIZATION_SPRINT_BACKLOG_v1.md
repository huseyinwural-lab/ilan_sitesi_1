# P9 Optimization Sprint Backlog

**Document ID:** P9_OPTIMIZATION_SPRINT_BACKLOG_v1  
**Date:** 2026-02-13  
**Sprint Goal:** Reduce Search P95 from 870ms to < 200ms.

---

## 1. High Priority (Must Do)
- [ ] **DB Migration:** Add `ix_la_attr_val_listing` composite index.
- [ ] **DB Migration:** Add `ix_listings_cat_status_price` composite index.
- [ ] **Backend Refactor:** Implement `asyncio.gather` for parallel facet queries in `search_routes.py`.
- [ ] **Infrastructure:** Install/Configure Redis service in Docker Compose (if not fully integrated).
- [ ] **Backend Feature:** Implement `RedisCache` service and `@cache` decorator.

## 2. Medium Priority
- [ ] **Search:** Implement Trigram Index for text search (`q=...`).
- [ ] **Frontend:** Optimistic UI updates for filters (don't wait for API to toggle checkbox visual).

## 3. Low Priority
- [ ] **Pre-computation:** Materialized View for "Empty Search" stats.

---

**Estimated Effort:** 1 Sprint (1 Week).
