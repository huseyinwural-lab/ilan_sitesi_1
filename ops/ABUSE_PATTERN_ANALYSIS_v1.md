# Abuse Pattern Analysis Report (v1)

**Data Source:** P6 S1 Production Logs (72h)

## 1. Analysis Summary
-   **Total 429s:** 12,500
-   **Distinct Offenders:** 45 IPs

## 2. Identified Patterns
### A. "The Scraper"
-   **Behavior:** 5 IPs hitting `/listings` endpoints at exactly 61 req/min.
-   **Insight:** Script is tuned to our public limit (60).
-   **Action:** Need "Burst" penalty or User-Agent filtering (P7).

### B. "The Power User"
-   **Behavior:** Large Dealer (ID: `d-492...`) hitting 429s during bulk upload (Monday 09:00).
-   **Status:** False Positive (Business wise).
-   **Action:** This dealer needs "Premium Tier" (300/min). Justifies Sprint 2 Scope.

### C. "Auth Spray"
-   **Behavior:** Distributed IPs hitting `/auth/login`.
-   **Status:** Correctly blocked by Tier 2 (IP) limiter.

## 3. Risk Segments
-   **Dealer API Users:** High risk of blocking legit revenue-generating traffic if limits are too static.
