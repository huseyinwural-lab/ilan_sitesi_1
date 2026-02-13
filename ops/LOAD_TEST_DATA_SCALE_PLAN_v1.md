# Load Test Data Scale Plan v1

**Goal:** Simulate Production Volume.

## 1. Method: Synthetic Duplication
-   **Source:** Seed v6 (200 Listings).
-   **Multiplier:** x50.
-   **Strategy:**
    -   Loop 50 times.
    -   Copy existing listing attributes.
    -   Mutate: `id`, `title` (Append index), `price` (Random jitter).
    -   Keep `category` and `attributes` distribution (to stress Facets).

## 2. Targets
-   **10k Listings:** Baseline for Query Plan.
-   **50k Listings:** Stress Test.
