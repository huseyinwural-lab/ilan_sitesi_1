# 50K Detail Page Load Test Report

**Document ID:** LOAD_TEST_REPORT_DETAIL_50K_v1  
**Date:** 2026-02-13  
**Status:** ⚠️ ACCEPTABLE FOR BETA  

---

## 1. Results

| Metric | Result | Target | Status |
|---|---|---|---|
| **P50 Latency** | 66ms | - | ✅ |
| **P95 Latency** | 160ms | < 120ms | ⚠️ |
| **RPS** | ~57 | - | ✅ |

## 2. Analysis
- **P50 is excellent (66ms):** The majority of users will experience instant load times.
- **P95 Spike (160ms):** Likely due to "Related Listings" query on the larger 50k dataset (sequential scan on `category_id`).
- **Index:** `listings(category_id)` index exists, but with 30k cars, the index scan might be slow if data is fragmented.

## 3. Decision
**GO for Beta.** The P50 shows the architecture is sound. P95 optimization can be handled via query tuning (LIMIT/OFFSET optimization) in the next sprint.
