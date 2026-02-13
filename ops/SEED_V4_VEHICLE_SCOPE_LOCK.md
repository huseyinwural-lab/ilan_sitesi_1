# Seed v4 Vehicle Scope Lock

**Target:** Vehicle Module Standardization (EU)
**Date:** 2026-03-16

## 1. Segments (Binding Strategy)
-   **Global:** `vehicle` (Root)
    -   Attributes: `brand`, `model`, `year`, `km`, `condition`, `warranty`, `swap`.
-   **Cars:** `cars`, `used-cars`, `new-cars`
    -   Attributes: `fuel_type`, `gear_type`, `body_type`, `engine_power_kw`, `engine_capacity_cc`, `drive_train`, `emission_class`, `inspection_valid`, `air_condition`, `navigation`, `leather_seats`, `sunroof`, `parking_sensors`.
-   **Moto:** `motorcycles`
    -   Attributes: `moto_type`, `engine_capacity_cc`, `engine_power_kw`, `abs`.
-   **Commercial:** `vehicles` (Wait, need to check if we have a separate 'commercial-vehicle' slug or if it's under vehicles).
    -   *Correction:* In v1 seed, `vehicle` root had `cars` and `motorcycles`. We need to add/verify `commercial-vehicles` category if missing, or bind to `vehicles` general if no specific cat.
    -   *Check:* v1 tree had `vehicle -> cars`, `vehicle -> motorcycles`. No commercial vehicle branch yet?
    -   *Action:* Seed script will create `commercial-vehicles` category if missing.
    -   Attributes: `comm_vehicle_type`, `load_capacity_kg`, `box_type`.

## 2. Localization
-   TR, DE, FR for all labels/options.

## 3. Execution
-   Script: `seed_production_data_v4.py`
-   Mode: Upsert (Safe for existing data).
