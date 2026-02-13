# Vehicle Filter Query Plan Analysis v1

**Goal:** Ensure Master Data does not slow down search.

## 1. Test Queries
### A. Brand Filter
```sql
EXPLAIN ANALYZE SELECT * FROM listings WHERE make_id = 'uuid';
```
*Expectation:* Index Scan using `ix_listings_make_id`. Cost < 10.

### B. Brand + Model Filter
```sql
EXPLAIN ANALYZE SELECT * FROM listings WHERE make_id = 'uuid' AND model_id = 'uuid';
```
*Expectation:* Index Scan using `ix_listings_model_id` (Postgres handles overlapping indexes well, or composite index usage).

### C. Category + Brand
```sql
EXPLAIN ANALYZE SELECT * FROM listings WHERE category_id = 'uuid' AND make_id = 'uuid';
```
*Expectation:* Bitmap Heap Scan combining indexes.

## 2. Thresholds
-   **Seq Scan:** FORBIDDEN on `listings`.
-   **Execution Time:** < 5ms (for 120 rows).
