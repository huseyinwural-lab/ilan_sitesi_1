# P9 Search P95 Root Cause Analysis

**Document ID:** P9_SEARCH_P95_ROOT_CAUSE_ANALYSIS_v1  
**Date:** 2026-02-13  
**Status:** 🔍 ANALYZED  

---

## 1. Problem
Load tests on the 50k dataset revealed a **P95 latency of 871ms** for the Search API (`GET /api/v2/search`). This exceeds the 150ms target by nearly 6x.

## 2. Query Analysis (Slowest Path)

### Query Signature
The bottleneck is the **Facet Aggregation Query** which runs for *each* active filterable attribute (e.g., brand, fuel_type, body_type).

```sql
SELECT value_option_id, count(*)
FROM listing_attributes la
WHERE la.attribute_id = 'uuid...'
AND la.listing_id IN (
    -- Subquery filtering main listings (Price, Category, Status)
    SELECT id FROM listings WHERE ...
)
GROUP BY value_option_id
```

### Execution Plan Issues (EXPLAIN ANALYZE)
1. **Sequential Scan on Subquery:** The `IN (...)` clause forces the DB to materialize the filtered listing set first.
2. **Missing Composite Index:** The `listing_attributes` table is scanned using `attribute_id` index, but then needs to cross-check `listing_id`.
3. **Loop Overhead:** This query runs `N` times (where N = number of filterable attributes, approx 8-10 for Cars).
   - 10 queries x 80ms each = 800ms total.

---

## 3. Impact
- **CPU:** Linear increase with concurrent searches.
- **Scalability:** Unusable beyond 100 concurrent users without caching.

---

## 4. Proposed Solution (P9)
1. **Composite Indexing:** 
   - Add `ix_listing_attributes_attr_listing` on `(attribute_id, listing_id) INCLUDE (value_option_id)`.
   - This allows "Index Only Scan" for counting.
2. **Parallel Execution:** Run facet queries in parallel using `asyncio.gather` instead of sequential loop.
3. **Redis Caching:** Cache the result of the aggregation for common queries (Empty search, Category roots).

**Estimated Improvement:** 870ms -> ~150ms.
