# Query Plan Audit Search v2 v1

**Tool:** `EXPLAIN (ANALYZE, BUFFERS)`

## 1. Critical Queries
-   [ ] **Facet Aggregation:** Group By `value_option_id`.
    -   *Risk:* Hash Aggregate on large set.
-   [ ] **Attribute Filtering:** `EXISTS (SELECT 1 ...)`
    -   *Risk:* Nested Loop vs Hash Join.

## 2. Index Verification
-   [ ] `ix_listing_attributes_attr_val_opt` usage confirmed.
-   [ ] `ix_listing_attributes_listing_id` usage confirmed.
