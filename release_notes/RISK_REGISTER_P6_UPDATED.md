# Risk Register (P6 Updated)

**Phase:** P6 Sprint 1
**Date:** 2026-02-13

| ID | Risk | Severity | Trigger | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-006** | **Redis SPOF (Fail-Open Abuse)** | High | Redis Cluster down. | **Fail-Open:** Allow traffic. **Alert:** P1 Alert to Ops. Limit impact via WAF if DDoS. | DevOps |
| **R-007** | **Log Volume Explosion** | Medium | High traffic spike. | **Sampling:** Aggressive sampling on INFO logs. **Retention:** Shorten Hot retention. | DevOps |
| **R-010** | **Rate Limit TTL Drift** | Low | Redis/App clock skew. | **NTP:** Sync clocks. **Logic:** Rely on Redis server time (Lua scripts) for expiry. | Backend |
| **R-011** | **Shadow Mode Misinterpretation** | Medium | Mismatch > 5%. | **Analysis:** Distinguish between "Distributed Sync" diffs (expected) vs Logic bugs. | Backend |
| **R-012** | **Key Explosion** | Medium | DDoS with random IPs. | **Eviction:** `volatile-lru` ensures old keys drop. **Monitoring:** Alert on Key Count > 1M. | Security |
