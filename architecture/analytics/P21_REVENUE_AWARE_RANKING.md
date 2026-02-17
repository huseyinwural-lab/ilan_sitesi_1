# P21: Revenue-Aware Ranking & Experimentation

## 1. Objective
To maximize ARPU (Average Revenue Per User) without degrading user experience, by boosting monetization-driving listings in recommendations.

## 2. Monetization Boost Policy

### 2.1. Tiers
1.  **Showcase (Platinum)**:
    *   **Boost**: Guaranteed visibility in top 3 slots or interleaved every 5 items.
    *   **Weight**: Highest priority.
2.  **Premium (Gold)**:
    *   **Boost**: Sorted above organic listings within the same relevance band.
    *   **Weight**: Medium priority.
3.  **Organic (Standard)**:
    *   **Boost**: None. Sorted by relevance/recency.

### 2.2. Implementation (V1)
Since we use SQL for candidate generation, we use **deterministing sorting**:
`ORDER BY is_showcase DESC, is_premium DESC, created_at DESC`

## 3. A/B Test Framework

### 3.1. Experiment Definition
We will assign users to buckets based on `user_id` hash.

| Group | Allocation | Strategy |
| :--- | :--- | :--- |
| **Control (A)** | 50% | Pure Affinity + Recency (No commercial boost) |
| **Treatment (B)** | 50% | Revenue-Aware (Showcase/Premium Boost) |

### 3.2. Tracking
Every recommendation response includes `experiment_id` in metadata.
*   **Metric**: `CTR` (Click-Through Rate) per group.
*   **Guardrail**: If `CTR(B) < CTR(A) * 0.9`, rollback.

## 4. API Changes
`GET /api/v2/mobile/recommendations`
*   **Header**: `X-Experiment-Group` (Optional override for QA).
*   **Response**:
    ```json
    "meta": {
      "experiment": "revenue_boost_v1",
      "group": "B"
    }
    ```
