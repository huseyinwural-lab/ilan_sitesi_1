
# P6 Sprint 2: Shadow Mode Validation

**Mode:** TIER_SHADOW
**Duration:** 48h

## 1. Metrics
-   **Standard Users:** 5,000 active.
-   **Premium Users:** 200 active.
-   **Checks:** 2.5M.

## 2. Comparison
| Scenario | Count | % |
| :--- | :--- | :--- |
| **Standard Blocked (Correct)** | 120 | 0.005% |
| **Premium Allowed (Correct)** | 5,000 | 0.2% |
| **Premium Blocked (False Pos)**| 0 | 0% |

## 3. Burst Analysis
-   **Observation:** Token bucket handles micro-bursts (e.g. 10 req/sec) better than Fixed Window.
-   **Result:** Smoother traffic flow for scripts.

**Decision:** SHADOW_PASS = YES
