# Load Test Report Search v2 v1

**Status:** PENDING

## 1. Scenarios
-   **A (Browse):** `GET /search?category=smartphones&page=1..5`
-   **B (Filter):** `GET /search?attrs={"brand":["apple"]}`
-   **C (Complex):** `GET /search?attrs={...} + q=iphone`

## 2. Results (Baseline)
| Metric | Scenario A | Scenario B | Scenario C |
| :--- | :--- | :--- | :--- |
| **p50** | TBD | TBD | TBD |
| **p95** | TBD | TBD | TBD |
| **RPS** | TBD | TBD | TBD |
