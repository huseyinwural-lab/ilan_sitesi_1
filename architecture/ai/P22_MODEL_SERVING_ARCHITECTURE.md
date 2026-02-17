# P22: Model Serving Architecture

## 1. Overview
This document defines how we manage, deploy, and serve Machine Learning models for ranking listings in the mobile feed.

## 2. Model Registry
We need a database table to track model versions and their status.

### 2.1. Schema: `ml_models`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `version` | String | e.g., "v1.0.0-xgboost" |
| `is_active` | Boolean | Only one model active at a time (Canary) |
| `metrics` | JSONB | e.g., `{"ndcg": 0.85, "precision": 0.2}` |
| `file_path` | String | Path to `.pkl` or `.json` model file |
| `created_at` | DateTime | Training timestamp |

## 3. Ranking Switch Policy
The `RecommendationService` will act as the switch.

**Logic Flow:**
1.  **Candidate Generation:** Fetch 100-200 candidates using Rule-Based logic (Fast SQL).
2.  **Switch Check:** Is Feature Flag `ENABLE_ML_RANKING` on? Is there an active `MLModel`?
3.  **Re-Ranking (if ML ON):**
    *   Hydrate features for User + Candidates.
    *   Call `MLServingService.predict(features)`.
    *   Sort candidates by Score DESC.
    *   Take Top N.
4.  **Fallback (if ML OFF):** Return candidates sorted by SQL logic.

## 4. Latency Budget
*   **Total Endpoint Budget:** 200ms.
*   **Candidate Gen (SQL):** 50ms.
*   **Feature Hydration:** 50ms (Redis/Memcached needed in future).
*   **Inference:** 20ms.
*   **Network:** 80ms.

## 5. Rollout Strategy
*   **Stage 1 (Shadow Mode):** Run ML inference asynchronously, log results, but return Rule-Based. Compare rankings offline.
*   **Stage 2 (Canary):** Enable for internal users or 5% traffic.
*   **Stage 3 (Full):** 100% Traffic.
