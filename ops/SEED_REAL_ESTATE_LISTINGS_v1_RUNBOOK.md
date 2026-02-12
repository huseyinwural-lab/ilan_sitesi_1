# Seed Real Estate Listings v1 Runbook

**Script:** `app/backend/scripts/seed_real_estate_listings.py`

## 1. Execution Logic
1.  **Fetch Context:** Load existing Users, Dealers, Categories, Attributes.
2.  **Clean Old:** Delete listings created by this script (identified by `audit_logs` batch_id or title pattern).
3.  **Generate:** Loop through templates.
    -   Select Random Owner (Dealer > User).
    -   Select Random Category (leaf node).
    -   Generate JSONB Attributes based on Template.
    -   Generate Title/Desc based on Locale (faker).
4.  **Insert:** Bulk Insert Listings.
5.  **Log:** Record `SEED_REAL_ESTATE_V1` in Audit Log.

## 2. Safety
-   Requires `--allow-prod` for Production (Blocked by default).
-   Upsert logic: If listing with same specialized slug/ref exists, update it.

## 3. Currency
-   **DE/FR:** EUR
-   **TR:** TRY (or EUR if configured as default for demo consistency). *Decision: Use EUR for global consistency in this Seed.*
