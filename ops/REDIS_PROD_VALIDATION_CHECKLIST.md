# Redis Production Validation Checklist

**Component:** Redis Infrastructure
**Role:** Distributed Rate Limit & Cache Store

## 1. High Availability & Failover
- [ ] **Multi-AZ:** Deployment spans at least 2 Availability Zones.
- [ ] **Failover Test:** Manual failover triggered; app recovers connection within < 30s.
- [ ] **Persistence:** RDB enabled (Snapshot) + AOF (Append Only File) active.

## 2. Resource Limits
- [ ] **Connection Limit:** Set to > (Max Pods * Pool Size * 2). Suggested: 5000+.
- [ ] **Max Memory Policy:** `volatile-lru` (Evict keys with TTL first).
- [ ] **Memory Alert:** Alarm at 70% memory usage.

## 3. Performance Configuration
- [ ] **Timeout:** Connection timeout set to 2s, Read timeout 200ms.
- [ ] **Slowlog:** Threshold set to 10ms (10000 microseconds).
- [ ] **Encryption:** TLS In-Transit enabled (Backend configured with `rediss://`).

## 4. Monitoring
- [ ] **Metrics:** Metrics (CPU, Memory, Connections, Evictions) exporting to Dashboard.
- [ ] **Access:** Security Group restricts access strictly to Backend Cluster CIDR.

**Status:** ⬜ PASS | ⬜ FAIL
*(Must be PASS before enabling Rate Limit integration)*
