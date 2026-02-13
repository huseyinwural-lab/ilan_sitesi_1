# Vehicle Master Data Scope v1

**Goal:** Establish a Production-Grade Vehicle Master Data Management (MDM) system.
**Status:** LOCKED

## 1. Scope
-   **Entities:** `Make` (Brand) and `Model`.
-   **Transition:** Move away from static `AttributeOption` lists to dedicated DB tables.
-   **Coverage:**
    -   **Markets:** DE (Primary), TR, FR.
    -   **Segments:** Passenger Cars, Motorcycles, Commercial Vehicles.
-   **Currency:** Monthly updates guaranteed.

## 2. Success Criteria
-   Admin can search/edit Brands and Models.
-   Models are strictly linked to Brands (Dependent).
-   Listings reference `make_id` and `model_id` (FK) instead of string values.
-   Seed v4 listings are successfully migrated to this new structure.

## 3. Temporary Status
-   Current listings (Seed v4) use `brand` (string) and `model` (string) in `attributes` JSONB.
-   **Plan:** These will be migrated to `make_id` columns (or standardized JSON keys) in the next sprint.
