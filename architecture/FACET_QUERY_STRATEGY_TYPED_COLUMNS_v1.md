# Facet Query Strategy Typed Columns v1

**Approach:** JOIN + Group By on Typed Tables.

## 1. Filtering Logic
-   **Select:** `JOIN listing_attributes la ON l.id = la.listing_id WHERE la.attribute_id = '...' AND la.value_option_id IN (...)`
    -   *Optimization:* For multiple attribute filters, use `INTERSECT` or multiple `EXISTS` subqueries?
    -   *Decision:* Multiple `EXISTS` clauses usually perform better than multiple JOINs for filtering.
    -   `WHERE EXISTS (SELECT 1 FROM listing_attributes la WHERE la.listing_id = l.id AND ...)`

## 2. Facet Aggregation Logic
-   **Query:** For each filterable attribute in the category:
    ```sql
    SELECT ao.value, ao.label, count(*)
    FROM listing_attributes la
    JOIN attribute_options ao ON la.value_option_id = ao.id
    WHERE la.attribute_id = '...' 
    AND la.listing_id IN (SELECT id FROM filtered_listings) -- Post-filter aggregation
    GROUP BY ao.value, ao.label
    ```
-   **Optimization:** Aggregating on the whole result set can be slow.
-   **Limit:** Only return facets for the top N attributes or active category attributes.

## 3. Text Search
-   Use `ilike` on `listings.title` for MVP. Move to Full-Text Search (tsvector) in P8.
