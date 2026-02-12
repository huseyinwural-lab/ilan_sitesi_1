# Risk Register (P6 Update)

**Date:** 2026-02-12

| ID | Risk | Severity | Mitigation Strategy | Owner |
|:---|:---|:---|:---|:---|
| **R-006** | **Redis SPOF:** If Redis fails, Rate Limiting stops working or blocks traffic. | High | **Strategy:** Fail-Open Policy. If Redis down, allow traffic. Log Error. | DevOps |
| **R-007** | **Log Volume:** Switching to JSON structured logs + Tracing might spike storage costs. | Medium | **Strategy:** Sampling (keep 100% errors, 10% success logs) if needed. | DevOps |
| **R-008** | **Key Explosion:** Malicious actors generating random IPs creates millions of Redis keys. | Medium | **Strategy:** Redis `volatile-ttl` eviction policy + Max Memory setting. | Security |
| **R-009** | **Latency:** Redis round-trip adds overhead to every request. | Low | **Strategy:** Use async `redis-py` + Pipelining. Timeout set to 200ms. | Backend |
