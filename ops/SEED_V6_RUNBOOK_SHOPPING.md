# Seed v6 Runbook Shopping

**Goal:** Populate Shopping Vertical (Attributes + Data).

## 1. Execution Sequence
1.  **Migration:** Create `listing_attributes` table (if new decision implemented) OR leverage existing `attributes` table if upgrading.
    -   *Decision:* We stick to the approved "Single Table + Typed Columns" decision.
    -   *Action:* Create migration for `listing_attributes` table.
2.  **Master Data:** Insert Attributes (`brand`, `storage`, `size`, `color`...) and Options.
3.  **Binding:** Link Attributes to Categories.
4.  **Listings:** Generate 60 High-Quality Listings using Template Logic.

## 2. Environment
-   **Staging:** Run with `--clean` first.
-   **Prod:** Run with `--allow-prod` (No clean).

## 3. Idempotency
-   Use `upsert` logic for Attributes/Options based on `key`.
-   Use `seed_batch_id` to track Listings.
