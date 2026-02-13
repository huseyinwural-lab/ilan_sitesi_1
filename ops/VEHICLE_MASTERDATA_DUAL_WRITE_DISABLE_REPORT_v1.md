# Vehicle Master Data Dual Write Disable Report

**Status:** PLANNED

## 1. Action
-   Update `ListingService` to STOP writing `brand` and `model` to `attributes` JSONB.
-   Rely exclusively on `make_id` and `model_id` columns.

## 2. Verification
-   Create new listing via API.
-   Inspect DB `attributes` column.
-   Confirm `brand` key is missing.

## 3. Backward Comp
-   Legacy readers might break if they rely on JSONB.
-   *Mitigation:* Update Serializer to inject `brand: make.name` into response payload dynamically if needed, NOT in DB.
