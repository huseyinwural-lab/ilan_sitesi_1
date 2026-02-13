# Seed Real Estate Listings v3 Changelog

**Goal:** Align Listing Data with EU Attribute Standards (Seed v3).

## 1. Logic Changes
-   **Room Count:**
    -   Generator now selects from `["1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "6", "7+"]`.
    -   Removed `1+1`, `2+1` logic.
-   **Kitchen:**
    -   Added `has_kitchen` (Boolean).
    -   Logic: True for 95% of Residential, False for some studios.
-   **Cleanup:**
    -   Script deletes all previous listings to ensure clean state.

## 2. Validation
-   Ensures attributes match the `Category` binding (e.g. Commercial listings do not get `has_kitchen`).
