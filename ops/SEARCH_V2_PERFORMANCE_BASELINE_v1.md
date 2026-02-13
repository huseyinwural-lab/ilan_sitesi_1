# Search v2 Performance Baseline v1

**Target:** < 150ms p95 Latency.

## 1. Index Checklist
-   [x] `listings`: `(status, module, country)` - Composite.
-   [x] `listing_attributes`: `(listing_id, attribute_id)` - Coverage.
-   [x] `listing_attributes`: `(attribute_id, value_option_id)` - Filtering Selects.
-   [x] `listing_attributes`: `(attribute_id, value_number)` - Filtering Ranges.

## 2. Synthetic Load Plan
-   Since seed data is small (200 items), we rely on `EXPLAIN ANALYZE` cost rather than raw duration for scalability projection.
-   **Goal:** Ensure Query Plan uses Index Scans, not Seq Scans.
