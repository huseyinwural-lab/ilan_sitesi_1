# Tier Limit Canary Execution Report

**Date:** 2026-02-17
**Status:** PLANNED

## 1. Strategy
-   **Flag:** `TIER_LIMIT_CANARY=True`
-   **Scope:** Apply Tier Logic only to Users ending in `0` (10% sample).
-   **Others:** Continue using global `60/min`.

## 2. Validation
-   **Check:** Monitor `rate_limit_tier_distribution` metric. Should see ~10% of traffic tagged with Tiers.
-   **Check:** Verify Premium Dealers in the 10% group are NOT blocked at 60.

## 3. Success Criteria
-   Redis CPU < 20% increase (Lua script overhead).
-   No increase in 5xx errors (Context resolution failures).
-   Premium throughput > 60 verified.
