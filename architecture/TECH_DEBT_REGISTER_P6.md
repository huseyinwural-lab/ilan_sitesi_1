# Technical Debt Register (P6)

**Updated:** 2026-02-16

## High Priority (Must Fix in P6)
1.  **Redis SPOF Risk:** While Fail-Open exists, we rely heavily on Redis.
    -   *Mitigation:* Chaos testing & robust failover configs.
2.  **Alert Thresholds:** Currently static. Need dynamic baselining (Anomaly Detection) as traffic grows.

## Medium Priority
3.  **Key Cardinality:** Random IP attacks could fill Redis memory.
    -   *Mitigation:* Aggressive TTL is set, but need specific alert for `dbsize`.
4.  **Log Volume Cost:** JSON logs are larger than text.
    -   *Mitigation:* Implement sampling for `200 OK` INFO logs.

## Low Priority
5.  **Library Dependency:** `redis-py` version is pinned. Need auto-update strategy.
6.  **Hardcoded Configs:** Some legacy defaults still in `config.py` vs Env Vars.
