# P23: ML Monitoring & Drift Detection Specification

## 1. Objective
To ensure the ML ranking models deployed in P22 maintain performance over time and to detect "Silent Failures" (Model Drift).

## 2. Prediction Logging
Every inference call must be logged for offline analysis.

### 2.1. Schema: `ml_prediction_logs`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `request_id` | UUID | Trace ID from API |
| `model_version` | String | e.g., "v1-mock" |
| `user_id` | UUID | Who saw the ranking |
| `candidate_count` | Integer | How many items ranked |
| `top_score` | Float | Max score (sanity check) |
| `execution_time_ms` | Float | Latency tracking |
| `created_at` | DateTime | Timestamp |

*Note: Storing full feature vectors per request is expensive. We store metadata + sample inputs or use a separate "Feature Store Snapshot" approach.*

## 3. Data Drift Detection
**Drift**: When production data distribution diverges from training data.

### 3.1. Metrics to Monitor
*   **Score Distribution**: Mean/Median score per hour. If scores suddenly drop to 0.0, model is broken.
*   **Feature Distribution**: e.g., `price` average. If inflation happens, model might undervalue high-price items.
*   **CTR by Model**: Click-Through Rate per `model_version`.

### 3.2. Alerting Rules
*   **Critical**: `P95 Latency > 200ms` -> Fallback to Rule-Based.
*   **Warning**: `Score Mean < 0.1` (assuming range 0-1).

## 4. Dashboard (Admin)
*   **Live**: Requests/sec, Latency.
*   **Daily**: CTR Comparison (A/B), Drift Report.
