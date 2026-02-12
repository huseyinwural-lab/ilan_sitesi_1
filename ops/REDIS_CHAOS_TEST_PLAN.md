# Distributed RL Chaos Test Plan

**Objective:** Verify system resilience against Redis failures.
**Mode:** Planned Maintenance Window (Stage Environment first).

## Scenario 1: Redis Connection Timeout
-   **Action:** Introduce network latency (tc qdisc) > 200ms on Redis port.
-   **Expected Behavior:**
    -   Backend catches `RedisTimeoutError`.
    -   Rate Limiter triggers **Fail-Open** (Allow Request).
    -   Log: `event="rate_limit_fail_open"`.
    -   Alert: "Redis Latency Critical".
-   **User Impact:** No blocking, slight latency increase (up to timeout cap).

## Scenario 2: Connection Refused (Crash)
-   **Action:** Stop Redis Service.
-   **Expected Behavior:**
    -   Backend catches `ConnectionError`.
    -   Fail-Open immediately.
    -   Log: `event="rate_limit_redis_error"`.
-   **User Impact:** None (Traffic allowed).

## Scenario 3: Read-Only Replica Promotion
-   **Action:** Force AWS failover.
-   **Expected Behavior:**
    -   Brief period of "ReadOnlyError" on writes.
    -   App reconnects to new Primary within 30s.
    -   Counters might reset or persist (depending on AOF sync).

## Post-Test Checklist
- [ ] 5xx Rate remained < 1%.
- [ ] No users received 500 error due to Rate Limit logic.
- [ ] Alerts triggered successfully.
