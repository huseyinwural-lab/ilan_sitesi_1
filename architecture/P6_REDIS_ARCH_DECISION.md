# P6 Redis Architecture Decision

**Component:** Distributed Rate Limiter & Caching
**Date:** 2026-02-12

## 1. Deployment Model
**Decision:** Managed Primary-Replica (High Availability).
**Rationale:**
-   **Cluster** is overkill for Rate Limit counters (High complexity).
-   **Single Node** is a SPOF.
-   **Primary-Replica** offers automatic failover with sufficient write throughput for current scale.

## 2. Configuration Strategy
-   **Persistence:** `RDB` (Snapshots every 15 min) + `AOF` (Every second).
    -   *Reason:* Rate limit counters are ephemeral, strict durability (fsync always) kills performance. 1-second data loss in a crash is acceptable for rate limits.
-   **Eviction Policy:** `volatile-ttl` (Only expire keys with TTL).
-   **Timeout:** 200ms (Connect/Read).
    -   *Reason:* Rate limiting must be fast. If Redis is slow, fail open.

## 3. Rate Limiting Implementation
-   **Key Schema:** `rl:{namespace}:{identifier}` (e.g., `rl:login:ip:192.168.1.1`).
-   **TTL:** Keys MUST have a TTL equal to the Window size (e.g., 60s).
-   **Failover Strategy:** **Fail-Open**.
    -   If Redis is unreachable, log error and **ALLOW** the request.
    -   *Why?* Availability > Strict Rate Limiting (unless under active DDoS).

## 4. Circuit Breaker
-   If Redis error rate > 50%, disable Redis checks for 30 seconds and revert to In-Memory (Tier 2 only) or Allow All.
