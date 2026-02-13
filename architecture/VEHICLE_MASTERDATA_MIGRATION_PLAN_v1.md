# Vehicle Master Data Migration Plan v1

**Type:** Breaking Change (Schema & Logic)
**Target:** Vehicle Module (Cars, Moto, Commercial)

## 1. Schema Changes
### New Tables
-   `vehicle_makes`: Stores brands (BMW, Mercedes).
-   `vehicle_models`: Stores models (3 Series, C-Class).

### Modified Table: `listings`
-   Add `make_id` (UUID, Nullable).
-   Add `model_id` (UUID, Nullable).
-   *Existing JSONB `attributes` (brand, model) remain as DEPRECATED fallback.*

## 2. Compatibility Strategy (Dual Mode)
-   **Phase 1 (Hybrid):** Application reads `make_id` first. If NULL, falls back to `attributes['brand']`.
-   **Phase 2 (Migration):** Backfill script maps all strings to IDs.
-   **Phase 3 (Cutover):** Application writes to `make_id`. JSONB fields cleared or kept for audit.

## 3. Rollback
-   If new logic fails, set Feature Flag `VEHICLE_MASTER_DATA_ENABLED=False`.
-   App reverts to reading JSONB attributes.
