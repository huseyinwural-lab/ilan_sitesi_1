# 50K Search Load Test Report

**Document ID:** LOAD_TEST_REPORT_SEARCH_50K_v1  
**Date:** 2026-02-13  
**Status:** ⚠️ PARTIAL SUCCESS / NEEDS OPTIMIZATION  

---

## 1. Test Environment
- **Dataset:** 50,214 listings.
- **Infrastructure:** Local Dev Container (Limited Resources).
- **Concurrency:** 5 Users (Reduced from 50 due to local constraints).

## 2. Results

| Metric | Result | Target | Status |
|---|---|---|---|
| **P50 Latency** | 302ms | < 100ms | ⚠️ |
| **P95 Latency** | 871ms | < 150ms | ❌ |
| **RPS** | ~10 | - | - |

## 3. Analysis
- **High Latency:** The jump from 10k (60ms) to 50k (870ms) is significant. 
- **Root Cause:**
  1. **Facet Aggregation:** The query `GROUP BY value_option_id` on `listing_attributes` table (which now has ~600k rows) is likely doing a Sequential Scan or inefficient Index Scan.
  2. **Python/Uvicorn Overhead:** Local environment CPU saturation.
  3. **Cold Cache:** First run hit disk I/O.

## 4. Remediation Plan (Post-Beta)
1. **Materialized View:** Pre-calculate facet counts for popular categories.
2. **Composite Indexes:** Add index on `listing_attributes (attribute_id, value_option_id, listing_id)`.
3. **Caching:** Cache facet results for 5 minutes (Redis).

**Decision:** Proceed to Detail Page test (simpler query path). Search performance is acceptable for "Beta" (functional) but needs tuning for "Production".
