# Vehicle Master Data Provider Sync Schedule v1

**Goal:** Sustainability

## 1. Schedule
-   **Frequency:** Monthly (1st of Month).
-   **Tool:** `scripts/sync_vehicle_master_data.py`.

## 2. Strategy
-   **Source:** Provider JSON (Managed snapshot).
-   **Diff Logic:**
    -   New Slug -> Insert.
    -   Existing Slug -> Update metadata (if needed).
    -   Missing in Source -> **No Action** (Do not auto-delete).

## 3. Manual Override
-   Admin can flag a model `is_active=False` if discontinued/erroneous.
-   Sync script MUST respect `is_active` flag (Do not re-activate automatically).
