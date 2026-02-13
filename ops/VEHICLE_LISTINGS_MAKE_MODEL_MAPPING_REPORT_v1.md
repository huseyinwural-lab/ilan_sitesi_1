# Vehicle Listings Make/Model Mapping Report

**Process:** String -> UUID Migration

## 1. Auto-Match Logic
-   Lowercase comparison.
-   Fuzzy match ("Mercedes" == "Mercedes-Benz").

## 2. Unmapped Handling
-   If listing has "Togg" and Master Data doesn't -> **Create Temporary Make**?
-   *Decision:* NO. Fail migration for that row or mark "Unmapped".
-   *Action:* Pre-seed Master Data with ALL strings used in `seed_vehicle_listings.py`.

## 3. Execution Log
-   Total Listings: 120
-   Mapped: TBD
-   Unmapped: TBD
