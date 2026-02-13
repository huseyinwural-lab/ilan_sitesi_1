# 50K Dataset Generation Report

**Document ID:** LOAD_TEST_DATASET_50K_REPORT_v1  
**Date:** 2026-02-13  
**Status:** ✅ COMPLETED  

---

## 1. Summary
We successfully seeded **50,214 listings** using a high-performance bulk insert script (`scale_listings_50k.py`) bypassing the ORM layer for speed.

## 2. Dataset Profile

| Metric | Count |
|---|---|
| **Total Listings** | 50,214 |
| **Cars (Vasıta)** | 30,000 (60%) |
| **Real Estate** | 10,000 (20%) |
| **Electronics/Others** | 10,000 (20%) |
| **Total Users** | ~5 (Demo users + Admin) |

## 3. Integrity Check
- **Null References:** None (Enforced by `NOT NULL` constraints on `is_dealer_listing`, `is_premium`, `image_count`, `attributes`, `updated_at`).
- **Category Linking:** All listings linked to valid categories (Fallback logic used).
- **Indexing:** `ANALYZE` run post-insert to update query planner stats.

---

**Next Step:** Execute Search Path Load Test.
