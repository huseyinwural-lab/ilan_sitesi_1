# Postmortem & Guardrail: DEF-001

**Issue:** Tier Change Delay (60s).
**Root Cause:** Missing cache invalidation on Admin update.

## 1. Resolution
-   **Fix:** Added synchronous `redis.delete(ctx_key)` in Admin Route.
-   **Verification:** `test_fix_def001.py` passed.

## 2. Guardrails (Prevention)
-   **New Metric:** `tier_change_invalidation_latency_ms`.
-   **Alert:** If Tier Change happens BUT user hits Rate Limit with OLD limit logic within 60s -> Trigger Warning "Invalidation Failed".
-   **Code Review Rule:** Any Update to `DealerPackage` or `Subscription` MUST include `invalidate_context`.
