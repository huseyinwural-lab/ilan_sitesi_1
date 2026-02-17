# P23: SLA & Error Budget Policy

## 1. Service Level Agreement (SLA)

### 1.1. Availability
*   **Target**: 99.5% (Max 3.6 hours downtime/month).
*   **Definition**: Endpoint returns 2xx/4xx (not 5xx) within 2000ms.

### 1.2. Latency (Mobile Feed)
*   **P95 Target**: < 200ms.
*   **P99 Target**: < 500ms.

## 2. Fail-Safe Policy (Circuit Breaker)
To protect the core system from ML Service failures:

### 2.1. Logic
*   If `MLServingService` throws error OR takes > 100ms:
    *   **Action**: Catch exception immediately.
    *   **Fallback**: Return Rule-Based Recommendation (A/B Control Group).
    *   **Logging**: Log as `ML_FAILURE`.

### 2.2. Error Budget
*   We allow 5% of requests to fail-back to Rule-Based.
*   If > 5% fail, we disable ML Feature Flag automatically (Kill Switch).

## 3. Implementation
The `RecommendationService` is already designed with `try/except` blocks (implicit in previous code, but needs explicit hardening). We will add a timeout wrapper.
