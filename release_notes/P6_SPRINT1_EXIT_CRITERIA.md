# P6 Sprint 1 Exit Criteria

**Sprint Goal:** Distributed Scale & Observability Foundation.

## 1. Mandatory Conditions (Gates)
-   [ ] **Redis Stability:** p95 Latency < 5ms over 48h.
-   [ ] **Shadow Parity:** Rate Limit V2 (Redis) matches V1 (Memory) within 5% tolerance.
-   [ ] **Log Hygiene:** 100% of Production logs are Valid JSON. No plaintext leaks.
-   [ ] **Correlation:** `request_id` present in 100% of sampled traces.
-   [ ] **No Regression:** Pricing Gate (409) and Expiry Job functioning normally.

## 2. Approval
Only when ALL items are checked can we proceed to **Enforce Distributed Rate Limiting** and close Sprint 1.

**Target Closure:** T+48h (After Shadow Data Collection).
