# Attribute Indexing Guide v1

**Database:** PostgreSQL 15+
**Table:** `listings`
**Column:** `attributes` (JSONB)

## 1. Indexing Strategy
To support high-performance filtering on dynamic attributes without creating 100 columns:

### A. GIN Index (Mandatory)
-   **Command:** `CREATE INDEX ix_listings_attributes ON listings USING GIN (attributes);`
-   **Purpose:** Fast containment queries (`@>`) and existence checks (`?`).
-   **Usage:** Boolean filters, some Select filters.

### B. Path Indices (Optimization for Range)
-   For high-cardinality Range queries (Price, m2), GIN can be slower than B-Tree.
-   **Recommendation:**
    -   `price` is already a dedicated column (Indexed).
    -   `m2_gross` is Critical. Create a functional B-Tree index:
        `CREATE INDEX ix_listings_attr_m2_gross ON listings (((attributes->>'m2_gross')::int));`
    -   *Apply this only for Top 3 Range Filters (m2, year, km).*

## 2. Future Scaling
-   **Materialized Columns:** If `room_count` filtering becomes slow (>100ms) at 1M+ listings, migration `2026_P8_materialize_room_count` will move it to a real column.
-   **Current:** JSONB + GIN is sufficient for < 500k listings.
