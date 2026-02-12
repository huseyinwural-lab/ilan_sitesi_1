# Rate Limit Strategy V2 Proposal

**Target:** P6 Sprint 2
**Goal:** Smart Abuse Prevention & Business Segmentation.

## 1. Problem
Current limits (v1) are static. A VIP Dealer publishing 500 cars/hour gets blocked same as a spammer.

## 2. Proposed Features
### A. Tiered Limiting (Business Logic)
-   **Standard Dealer:** 60/min.
-   **Premium Dealer:** 300/min (Configurable via DB).
-   **Integration:** Look up `DealerPackage.tier` during auth/limit check.

### B. Dynamic Scoring (Abuse Hardening)
-   **Concept:** Assign "Risk Score" to IPs.
-   **Input:** Failed Logins + 404 scans.
-   **Action:** If Risk > Threshold, reduce limit to 1/min (Jail).

### C. Burst Allowances
-   **Current:** Fixed Window (reset every minute).
-   **Proposed:** Token Bucket / Sliding Window.
-   **Benefit:** Allows short bursts (e.g., script startup) without blocking.

## 3. Analysis Needed
-   Review current `429` logs to identify legitimate "Burst" users.
-   Estimate Redis Lua script complexity for Token Bucket.
