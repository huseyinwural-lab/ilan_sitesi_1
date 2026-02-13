# Vehicle Master Data Provider Sync v1

**Strategy:** Provider-Driven Population.

## 1. Source Logic
-   For MVP/Demo speed, we simulate a "Provider" using a comprehensive JSON dataset (based on common EU taxonomy).
-   **Why:** Connecting to real TecAlliance/NHTSA requires API Keys/License immediately.
-   **Data:** `vehicle_master_data_seed.json` (Managed file acting as Provider).

## 2. Sync Logic
-   Script: `sync_vehicle_master_data.py`
-   Reads `json` -> Upserts to DB.
-   Updates `source_updated_at`.

## 3. Diff Report
-   Logs "New Makes: X, New Models: Y".
