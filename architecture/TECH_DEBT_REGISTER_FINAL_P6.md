# Technical Debt Register (Final P6)

**Status:** Handover to Maintenance Team

## 1. High Priority (Monitor Closely)
-   **Redis Dependency:** Application fails open if Redis dies. Consider local memory circuit breaker fallback for basic DDoS protection (Tier 2).

## 2. Medium Priority
-   **Lua Script Complexity:** Token Bucket logic is hard to debug. Ensure unit tests cover edge cases (clock skew).
-   **Log Volume:** JSON logs are verbose. Need compression in ingestion pipeline.

## 3. Low Priority
-   **Tier Hardcoding:** Tiers are ENUMs in code. Moving to pure DB-driven dynamic tiers would be flexible but complex.
