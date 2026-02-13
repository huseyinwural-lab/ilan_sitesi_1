# Public Beta Search Monitoring Baseline

**Document ID:** PUBLIC_BETA_SEARCH_MONITORING_BASELINE_v1  
**Date:** 2026-02-13  
**Status:** 📊 BASELINE SET  

---

## 1. Test Conditions
- **Dataset:** 50,214 listings.
- **Environment:** Local Dev Container (Limited Resources).
- **Concurrency:** 5 concurrent users.
- **Traffic:** Mixed (Browse, Filter, Text Search).

## 2. Baseline Metrics (Pre-Optimization)

| Metric | Value | Target (P9) | Status |
|---|---|---|---|
| **P50 Latency** | 302ms | < 100ms | ⚠️ |
| **P95 Latency** | 871ms | < 200ms | ❌ |
| **P99 Latency** | ~1000ms | < 500ms | ❌ |
| **Error Rate** | 0% | < 0.1% | ✅ |
| **Cache Hit Ratio** | 0% | > 80% | ❌ |

## 3. Bottleneck Identification
- **Database CPU:** High during facet aggregation loop.
- **Sequential Scan:** `listing_attributes` table access is inefficient.
- **Network:** Redis connection failures observed (Infrastructure gap).

## 4. Success Criteria for P9
Optimization will be considered successful if:
1. P95 drops below **200ms**.
2. Redis Cache Hit Ratio exceeds **80%** for repeated queries.
3. No functional regression in search results.
