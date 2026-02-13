# Vehicle Master Data Cutover Plan

**Phased Rollout**

## 1. Dual Read (Active)
-   API response includes `make` (obj) AND `attributes.brand` (string).
-   Frontend prefers `make` object if present.

## 2. Migration
-   Run Backfill Script.

## 3. Dual Write (Deprecation)
-   API writes to BOTH.
-   Logs warning if String writes used.

## 4. Cutover
-   Flag `VEHICLE_MASTER_DATA_STRICT = True`.
-   API rejects requests without `make_id`.
