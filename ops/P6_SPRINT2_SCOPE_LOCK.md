# P6 Sprint 2 Scope Lock

**Theme:** Business-Aware Traffic Control
**Duration:** 2 Weeks

## 1. In-Scope (Deliverables)
-   **Tiered Rate Limiting:**
    -   Standard Dealer: 60/min.
    -   Premium Dealer: 300/min (Based on Active Package).
    -   Admin: 1000/min.
-   **Burst Control:** Switch from Fixed Window to Sliding Window (Redis Lua) or Leaky Bucket to allow short bursts.
-   **Abuse Detection:** Automated reporting of IPs hitting limits > 10x/day.

## 2. Out-of-Scope
-   **ML Anomaly Detection:** No AI-based blocking yet.
-   **Client Fingerprinting:** Reliance on IP/Token only.
-   **Captcha:** No CAPTCHA integration in this sprint.

## 3. Key Dependencies
-   `DealerPackage` table (to read limits).
-   `Redis` (to store tier-specific counters).
