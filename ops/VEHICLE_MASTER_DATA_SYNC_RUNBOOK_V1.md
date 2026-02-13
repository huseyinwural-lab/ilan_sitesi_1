# Vehicle Master Data Sync Runbook v1

**Process:** Maintaining the Make/Model Database.

## 1. Sync Workflow (Automated)
1.  **Fetch:** `python scripts/sync_vehicle_master_data.py --source=nhtsa`
2.  **Normalize:** Convert names to Title Case, slugs to kebab-case.
3.  **Deduplicate:** Check against DB `slug`.
    -   If exists -> Update `year_end` / metadata.
    -   If new -> Insert.
4.  **Report:** Generate `sync_report_{date}.json`.

## 2. Manual "Force Sync"
-   **Trigger:** Missing model reported.
-   **Action:**
    1.  Ops runs sync script targeting specific Brand.
    2.  `python scripts/sync_vehicle_master_data.py --brand="Rivian"`

## 3. Schedule
-   **Cron:** Monthly (1st day).
-   **Monitoring:** Check log for "New Models Added".
