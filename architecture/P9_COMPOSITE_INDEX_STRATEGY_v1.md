# P9 Composite Index Strategy

**Document ID:** P9_COMPOSITE_INDEX_STRATEGY_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Strategy
To support high-performance filtering and faceting on 50k+ rows, we need to move from single-column indexes to composite (multi-column) indexes that cover the query predicates (WHERE) and sorting (ORDER BY) in a single B-Tree traversal.

## 2. New Indexes to Create

### 2.1. Listing Filtering
**Table:** `listings`
**Index:** `ix_listings_cat_status_price`
**Columns:** `(category_id, status, price)`
**Rationale:** Supports "Show active cars ordered by price". Covering index.

### 2.2. EAV Faceting (Critical)
**Table:** `listing_attributes`
**Index:** `ix_la_attr_val_listing`
**Columns:** `(attribute_id, value_option_id, listing_id)`
**Rationale:**
- `attribute_id`: First filter (we query by attribute).
- `value_option_id`: Group by target.
- `listing_id`: Used for JOIN/IN clause check.
- **Benefit:** Allows "Index Only Scan" for faceting counts, avoiding Heap access.

### 2.3. Text Search (Future)
**Table:** `listings`
**Index:** `ix_listings_title_trgm` (GIN)
**Columns:** `title gin_trgm_ops`
**Rationale:** `ilike '%text%'` is slow. Trigram index speeds up fuzzy search.

---

## 3. Rollout Plan
1. Create DB migration script (Alembic or raw SQL).
2. Run `CREATE INDEX CONCURRENTLY` (to avoid locking table in prod).
3. Verify with `EXPLAIN ANALYZE`.
