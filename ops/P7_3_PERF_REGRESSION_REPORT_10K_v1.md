# P7.3 Performance Regression Report (10k Dataset)

**Document ID:** P7_3_PERF_REGRESSION_REPORT_10K_v1  
**Date:** 2026-02-13  
**Status:** ✅ PASSED  

---

## 1. Test Environment
- **Dataset:** ~10,000 listings (Vehicles & Real Estate)
- **Database:** PostgreSQL 15
- **Concurrency:** Sequential requests (1 client), 50 iterations per scenario.
- **Warmup:** 1 request per scenario.

---

## 2. Results

| Scenario | P95 Latency | Avg Latency | Status |
|---|---|---|---|
| **Category Browse (Cars)** | 58.19ms | 56.38ms | ✅ |
| **Filter (Brand=BMW)** | 60.08ms | 57.26ms | ✅ |
| **Complex (Brand+Price)** | 58.99ms | 56.39ms | ✅ |
| **Deep Pagination (Page 5)** | 56.98ms | 54.82ms | ✅ |

**Threshold:** < 150ms P95

---

## 3. Analysis
- **Stability:** Latency is highly consistent (~55-60ms range). No spikes observed.
- **Database Efficiency:** Query plans confirm Index Scans are used effectively. EAV joins (`listing_attributes`) are performant at this scale.
- **Facet Generation:** Aggregation overhead is negligible (< 5ms delta between filtered and non-filtered queries).

## 4. Conclusion
The Public Search API v2 integration introduces **zero regression** compared to the P7.0 baseline. The system is ready for the next scale test (50k).
