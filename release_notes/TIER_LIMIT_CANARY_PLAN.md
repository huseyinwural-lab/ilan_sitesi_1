# Tier Limit Canary Plan

**Feature:** Dynamic/Tiered Rate Limits
**Target:** Production

## 1. Strategy
-   **Target:** `POST /listings` endpoint.
-   **Traffic:** 10% of requests (Random selection or specific Dealer ID whitelist).

## 2. Configuration
-   `RL_TIER_ENABLED = "Canary"`
-   `RL_CANARY_PERCENT = 10`

## 3. Rollback Triggers
-   **Latency:** Redis p95 > 10ms (Due to extra DB lookup for Tier).
-   **Errors:** 5xx > 0.1% (Logic error in Tier resolution).
-   **Complaint:** "I cannot publish" from VIP Dealer.

## 4. Success Criteria
-   Premium Dealer (test account) can exceed 60 req/min (up to 300).
-   Standard Dealer still blocked at 60.
-   No DB contention on `DealerSubscription` lookup.
