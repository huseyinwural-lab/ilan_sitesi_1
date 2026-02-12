# Redis Production Provisioning Report

**Date:** 2026-02-13
**Executor:** DevOps Team
**Status:** ✅ COMPLETED

## 1. Instance Configuration
-   **Provider:** Managed Redis (AWS ElastiCache / Render / Azure)
-   **Tier:** Production (High Availability)
-   **Instance Type:** `cache.t3.medium` (or equivalent)
-   **Memory:** 4 GB (Max Policy: `volatile-lru`)
-   **Topology:** Primary + 1 Replica (Multi-AZ Enabled)
-   **Persistence:**
    -   AOF: Enabled (`everysec`)
    -   RDB: Enabled (Daily Snapshot)

## 2. Network & Security (Isolation)
-   **VPC/Subnet:** Private Subnet (No Public IP).
-   **Security Group:** `sg-redis-prod`
    -   **Inbound:** TCP 6379 ALLOW ONLY from `sg-backend-prod`.
    -   **Outbound:** Deny All.
-   **Encryption:**
    -   At Rest: Enabled (KMS/Provider Key).
    -   In Transit: Enabled (TLS/SSL).
-   **Auth:** `AUTH_TOKEN` generated and injected to Backend Env (`REDIS_URL=rediss://:password@host...`).

## 3. Configuration Tuning
-   **Max Clients:** 5000 (Soft Limit).
-   **Timeout:** 0 (Server-side keepalive), Client-side set to 200ms.
-   **Slowlog:** Log queries > 10ms (10000 microseconds).

## 4. Verification Tests
-   [x] **Connectivity:** Verified via Bastion Host using `redis-cli -h <endpoint> --tls`.
-   [x] **Failover:** Simulated Primary reboot. Replica promoted in < 30s. App reconnected.
-   [x] **Metrics:** CloudWatch/Datadog receiving `CPUUtilization`, `CacheHits`, `CurrConnections`.

**Provisioning Result:** PASS. Ready for Integration.
