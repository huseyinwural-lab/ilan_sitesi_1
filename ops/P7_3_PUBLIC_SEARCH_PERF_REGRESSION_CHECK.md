# P7.3 Public Search Performance Regression Check

**Document ID:** P7_3_PUBLIC_SEARCH_PERF_REGRESSION_CHECK  
**Date:** 2026-02-13  
**Status:** 📋 PENDING VALIDATION  
**Sprint:** P7.3  

---

## Purpose

Validate that P7.3 Public UI integration does not degrade the performance achieved in P7.0 stabilization phase.

---

## Baseline (P7.0)

| Metric | P7.0 Result | Target |
|--------|-------------|--------|
| Q1: Category Paging | 1.7ms | <150ms |
| Q2: Attribute Filter | 0.4ms | <150ms |
| Q3: Facet Aggregation | 2.0ms | <150ms |
| Overall p95 | <5ms | <150ms |

**Reference:** `/app/release_notes/PHASE_CLOSE_P7_0_STABILIZATION.md`

---

## P7.3 Test Scenarios

### Scenario 1: Simple Category Browse

**Query:** `/api/v2/search?category=cars&limit=20`

| Metric | Baseline | P7.3 Result | Delta | Status |
|--------|----------|-------------|-------|--------|
| p50 | 1.0ms | ⏳ | | |
| p95 | 2.0ms | ⏳ | | |
| p99 | 3.0ms | ⏳ | | |

**Pass Criteria:** p95 < 10ms

---

### Scenario 2: Category + Single Filter

**Query:** `/api/v2/search?category=cars&attrs={"brand":"bmw"}&limit=20`

| Metric | Baseline | P7.3 Result | Delta | Status |
|--------|----------|-------------|-------|--------|
| p50 | 0.5ms | ⏳ | | |
| p95 | 1.5ms | ⏳ | | |
| p99 | 2.5ms | ⏳ | | |

**Pass Criteria:** p95 < 15ms

---

### Scenario 3: Category + Multiple Filters

**Query:** `/api/v2/search?category=cars&attrs={"brand":"bmw","fuel_type":"benzin"}&price_min=20000&price_max=80000&limit=20`

| Metric | Baseline | P7.3 Result | Delta | Status |
|--------|----------|-------------|-------|--------|
| p50 | 1.0ms | ⏳ | | |
| p95 | 3.0ms | ⏳ | | |
| p99 | 5.0ms | ⏳ | | |

**Pass Criteria:** p95 < 20ms

---

### Scenario 4: Facet-Heavy Category

**Query:** `/api/v2/search?category=real-estate&limit=20` (many attributes)

| Metric | Baseline | P7.3 Result | Delta | Status |
|--------|----------|-------------|-------|--------|
| p50 | 2.0ms | ⏳ | | |
| p95 | 4.0ms | ⏳ | | |
| p99 | 6.0ms | ⏳ | | |

**Pass Criteria:** p95 < 25ms

---

### Scenario 5: Pagination Deep Page

**Query:** `/api/v2/search?category=cars&page=50&limit=20`

| Metric | Baseline | P7.3 Result | Delta | Status |
|--------|----------|-------------|-------|--------|
| p50 | N/A | ⏳ | | |
| p95 | N/A | ⏳ | | |
| p99 | N/A | ⏳ | | |

**Pass Criteria:** p95 < 50ms (deep page allowed higher)

---

### Scenario 6: Text Search

**Query:** `/api/v2/search?q=bmw+3+series&limit=20`

| Metric | Baseline | P7.3 Result | Delta | Status |
|--------|----------|-------------|-------|--------|
| p50 | N/A | ⏳ | | |
| p95 | N/A | ⏳ | | |
| p99 | N/A | ⏳ | | |

**Pass Criteria:** p95 < 30ms

---

## Test Methodology

### Load Generation

```bash
# Using curl with timing
for i in {1..100}; do
  curl -s -w "%{time_total}\n" -o /dev/null \
    "${API}/api/v2/search?category=cars&limit=20"
done | sort -n | tail -5  # p95 approx
```

### Alternative: Apache Bench

```bash
ab -n 100 -c 10 "${API}/api/v2/search?category=cars&limit=20"
```

---

## Regression Thresholds

| Metric | Acceptable Delta |
|--------|------------------|
| p50 | +50% |
| p95 | +100% |
| p99 | +150% |

**Example:** If baseline p95 = 2ms, acceptable P7.3 p95 = 4ms

---

## Database State

| Metric | At Test Time |
|--------|--------------|
| Total Listings | 270 |
| Categories | 23 |
| Attributes | 57 |
| Vehicle Makes | 10 |
| Vehicle Models | 27 |

**Note:** Production will have more data; scale test planned for P7.4

---

## Index Health Check

Before performance test, verify indexes:

```sql
-- Check index usage
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;

-- Analyze tables
ANALYZE listings;
ANALYZE listing_attributes;
ANALYZE vehicle_makes;
ANALYZE vehicle_models;
```

---

## Results Summary

| Scenario | p95 Target | p95 Actual | Status |
|----------|------------|------------|--------|
| S1: Category Browse | <10ms | ⏳ | |
| S2: Single Filter | <15ms | ⏳ | |
| S3: Multiple Filters | <20ms | ⏳ | |
| S4: Facet Heavy | <25ms | ⏳ | |
| S5: Deep Page | <50ms | ⏳ | |
| S6: Text Search | <30ms | ⏳ | |

---

## Gate Status

**P7.3 cannot close until:**
- [ ] All scenarios tested
- [ ] No scenario exceeds p95 target
- [ ] No regression >100% from baseline
- [ ] Results documented in this file

---

## Escalation

If regression detected:
1. Document specific query and result
2. Run EXPLAIN ANALYZE on problematic query
3. Check for missing indexes
4. Consider query optimization before UI changes

---

## References

- P7.0 Query Plan Audit: `/app/ops/QUERY_PLAN_AUDIT_SEARCH_V2_10K_v1.md`
- Search API v2: `/app/backend/app/routers/search_routes.py`
- Index Strategy: `/app/architecture/ATTRIBUTE_INDEXING_GUIDE_v1.md`
