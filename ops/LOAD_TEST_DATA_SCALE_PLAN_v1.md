# Load Test Data Scale Plan v1

**Goal:** Create a realistic dataset for Search v2 performance validation.
**Status:** PENDING EXECUTION

## 1. Scale Targets
-   **Baseline:** Current ~200 listings (Seed v6).
-   **Target:** 10,000 Listings (50x Multiplier).
-   **Composition:**
    -   70% Real Estate (Heavy on Facets like Room Count, m2).
    -   30% Vehicles (Heavy on Make/Model Facets).

## 2. Methodology (Synthetic Duplication)
-   **Script:** `scripts/scale_listings_data.py`
-   **Logic:**
    1.  Fetch existing "High Quality" listings (Seed v6).
    2.  Loop 50 times.
    3.  Clone Listing + Attributes.
    4.  Mutate `price` (+/- 10%) to affect sorting.
    5.  Mutate `created_at` (Random past date) to affect sorting.
    6.  Insert Bulk.

## 3. Determinisim
-   Uses fixed random seed (`random.seed(42)`) to ensure reproducible datasets across runs.
