# Impact Analysis: DEF-001 Fix

**Change:** Synchronous Redis Delete on Admin Action.

## 1. Performance
-   **Latency:** Adds ~1-2ms to the *Admin Update Endpoint*.
-   **Throughput:** Negligible impact (Admin updates are rare events).
-   **Rate Limiter:** Next user request will be a Cache Miss (DB lookup) -> ~5ms latency penalty for *one* request. **Acceptable.**

## 2. Race Conditions
-   **Scenario:** Admin updates Tier while User is spamming requests.
-   **Outcome:**
    -   Req 1 (Old Tier) -> Allowed/Blocked based on old counter.
    -   Admin Update -> Clears Cache.
    -   Req 2 (New Tier) -> Cache Miss -> DB Fetch (New Tier) -> New Counter Key.
    -   **Result:** Correct behavior. Burst resets (User gets full new burst).

## 3. Security
-   **Risk:** Can an Admin deny service by spamming updates (Cache thrashing)?
-   **Mitigation:** Admin endpoints are rate-limited (Tier 1) and Audit Logged.

**Verdict:** Low Risk. Proceed with Fix.
