# Vehicle Listings Make/Model Migration Plan v1

**Migration:** Seed v4 (Attribute) -> Seed v5 (Master Data)

## 1. Analysis Phase
-   Scan all 120 existing listings.
-   Extract unique `attributes->>'brand'` and `attributes->>'model'`.
-   Create Mapping Table: `{"BMW": uuid, "320d": uuid}`.

## 2. Migration Execution
1.  **Populate Master Data:** Insert extracted Brands/Models into new Tables.
2.  **Update Listings:**
    -   Add columns `make_id` (UUID), `model_id` (UUID) to `listings` table (or keep in attributes but as IDs).
    -   *Decision:* Keep in `attributes` JSONB for flexibility, OR move to columns for relational integrity?
    -   *Verdict:* **Move to Columns.** `make_id`, `model_id` indexed columns are better for joins/filtering.
3.  **Backfill:** Update rows.

## 3. Verification
-   Query: `SELECT count(*) FROM listings WHERE make_id IS NULL`. Should be 0.
