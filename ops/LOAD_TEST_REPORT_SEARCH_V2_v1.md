# Load Test Report Search v2 v1

**Status:** PENDING EXECUTION

## 1. Environment
-   **DB:** PostgreSQL 15 (Local Container).
-   **Data:** 10k Listings.
-   **Tool:** Python Async Benchmark Script (`scripts/benchmark_search.py`).

## 2. Scenarios & Results
| Scenario | Latency p50 | Latency p95 | RPS | Status |
| :--- | :--- | :--- | :--- | :--- |
| **A: Simple Browse** | TBD | TBD | TBD | |
| **B: Facet Filter** | TBD | TBD | TBD | |
| **C: Complex Query** | TBD | TBD | TBD | |

## 3. Thresholds
-   **Goal:** p95 < 150ms.
-   **Fail Condition:** p95 > 500ms or Error Rate > 1%.
