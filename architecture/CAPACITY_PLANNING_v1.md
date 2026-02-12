# Capacity Planning (v1)

**Target Period:** Q2-Q3 2026

## 1. Redis Capacity
-   **Current Usage:** ~1.4GB (35% of 4GB).
-   **Key Growth Factor:** ~100 bytes per active user session.
-   **Projection:**
    -   50k Active Users -> ~5MB (Negligible).
    -   *Bottleneck is NOT Memory, but CPU/Network Ops.*
-   **Scale Trigger:** When Ops/Sec > 25,000 (Current capacity ~80k).

## 2. Database Capacity
-   **Log Growth:** ~5GB/day.
-   **Retention:** 30 days hot.
-   **Storage:** 150GB minimum required.
-   **Scale Trigger:** Disk usage > 70%.

## 3. Traffic Growth Scenarios
| Scenario | Impact | Action |
| :--- | :--- | :--- |
| **Normal Growth (10% MoM)** | None | Regular monitoring. |
| **Marketing Burst (2x Traffic)** | API Latency +20% | Vertical Scale Backend Pods (CPU). |
| **DDoS (100x Traffic)** | Redis Saturation | Enable WAF Shield. Disable Tier 1 Limiter (rely on IP limit). |

## 4. Multi-Region Readiness
-   **Current:** Single Region (Active-Passive).
-   **Requirement:** Redis replication across regions would be needed for Active-Active.
-   **Plan:** Defer until Q4 2026.
