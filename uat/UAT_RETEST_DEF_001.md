# Retest Plan: DEF-001

**Scenario:** Immediate Tier Upgrade

## Steps
1.  **Setup:** Create Dealer with `STANDARD` Tier.
2.  **Baseline:** Verify Limit is 60/min.
3.  **Action:** Call `PATCH /api/admin/dealers/{id}/tier` body=`{"tier": "PREMIUM"}`.
4.  **Verify 1 (DB):** Check `dealer_packages` link updated.
5.  **Verify 2 (Redis):** Check `rl:context:{id}` does NOT exist (Deleted).
6.  **Verify 3 (Limit):** Immediately send 61st request.
    -   *Expected:* 200 OK (Allowed).
    -   *Old Behavior:* 429 Too Many Requests.

## Success Criteria
-   Limit change is effective < 1 second after API response.
-   Audit log contains `tier_change`.
