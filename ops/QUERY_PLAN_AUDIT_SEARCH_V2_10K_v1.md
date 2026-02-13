# Query Plan Audit Search v2 (10k Dataset)

**Status:** PENDING
**Goal:** Analyze execution plans for critical search queries.

## 1. Test Queries
### Q1: Base Category Paging
-   **Scenario:** User browses "Smartphones".
-   **SQL:** `SELECT * FROM listings WHERE category_id = '...' ORDER BY created_at DESC, id DESC LIMIT 20`

### Q2: 1 Select Filter + Facets
-   **Scenario:** User filters Smartphones by Brand=Apple.
-   **SQL:** 
    -   Filter: `... WHERE EXISTS (SELECT 1 FROM listing_attributes WHERE ... value_option_id = '...')`
    -   Facet: `SELECT option_id, count(*) ... GROUP BY option_id`

### Q3: Complex (2 Select + 1 Range)
-   **Scenario:** Smartphones: Brand=Samsung, RAM=8GB, Price < 1000.
-   **SQL:** Multiple `EXISTS` clauses + Range on `price`.

### Q4: Inheritance Facets
-   **Scenario:** Search "Electronics". Facet includes "Brand" (Inherited) and "Screen Size" (Child).
-   **SQL:** Aggregation over a larger set of listings.

## 2. Expected Indexes
-   `ix_listings_category_id`
-   `ix_listing_attributes_attr_val_opt`
-   `ix_listing_attributes_listing_id`
