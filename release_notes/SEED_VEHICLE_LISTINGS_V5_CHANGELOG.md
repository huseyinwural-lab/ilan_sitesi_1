# Seed Vehicle Listings v5 Changelog

**Target:** Production-Grade Listings

## 1. Changes
-   **Source:** Uses `vehicle_makes` and `vehicle_models` tables instead of hardcoded arrays.
-   **Structure:**
    -   `make_id`: UUID
    -   `model_id`: UUID
-   **Content:**
    -   Ensures 100% match with Master Data.
    -   No "Free Text" brands.

## 2. Constraint
-   Script will FAIL if Master Data is empty.
-   **Prerequisite:** Run `sync_vehicle_master_data.py` (or seed equivalent) first.
