# P8 Detail Page Performance Regression Report

**Document ID:** P8_DETAIL_PAGE_PERF_REGRESSION_v1  
**Date:** 2026-02-13  
**Status:** ✅ PASSED  

---

## 1. Test Environment
- **Target:** `/api/v2/listings/{id}`
- **Aggregation Complexity:** 
  - Listing Base Data
  - User/Dealer Join
  - EAV Attributes (ListingAttributes + Options + Definitions)
  - Category Breadcrumb (Recursive)
  - Related Listings (Subquery)
- **Dataset:** ~10,000 Listings

---

## 2. Results

| Metric | Result | Target | Status |
|---|---|---|---|
| **P95 Latency** | 56.50ms | < 100ms | ✅ |
| **Avg Latency** | 51.11ms | - | ✅ |
| **Error Rate** | 0% | 0% | ✅ |

---

## 3. Analysis
- **EAV Optimization:** Attribute aggregation is performing well. The decision to fetch definitions separately and map in memory (instead of massive SQL join) proves effective.
- **Related Listings:** The additional query for related items (Limit 4) adds negligible overhead (< 5ms).
- **TTFB:** With ~50ms API response + ~20ms network overhead (local), TTFB is well within the 200ms budget.

## 4. Conclusion
The Detail Page API is highly performant and ready for production load.
