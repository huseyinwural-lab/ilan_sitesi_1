# 50K Dataset Scale Test Plan

**Document ID:** LOAD_TEST_PLAN_50K_v1  
**Date:** 2026-02-13  
**Status:** 🚀 IN PROGRESS  

---

## 1. Objective
Validate system stability, query performance, and indexing strategy under a medium-scale dataset (50,000 listings) to approve Public Beta launch.

**Target:** Mimic Day 1-30 post-launch data volume.

---

## 2. Data Generation Strategy

### 2.1. Volume Targets
- **Total Listings:** 50,000
- **Users:** 2,000 (Mix of Individual and Dealer)
- **Attributes (EAV Rows):** ~600,000 (Avg 12 attrs per listing)

### 2.2. Distribution Profile
To stress-test facet aggregation, we will use a non-uniform distribution:

| Category | Count | Purpose |
|---|---|---|
| **Cars (Vasıta)** | 30,000 (60%) | Facet Stress Test (High cardinality filters) |
| **Real Estate (Emlak)** | 10,000 (20%) | Attribute Density Test |
| **Electronics (Shopping)** | 5,000 (10%) | Deep Hierarchy Test |
| **Others** | 5,000 (10%) | General Noise |

### 2.3. Worst-Case Scenarios
- **Facet Explosion:** A "Brand" filter in Cars with 50+ options populated.
- **Range Queries:** Price and Year filtering on 30k subset.
- **Text Search:** "Sahibinden" wildcard search (Index scan test).

---

## 3. Execution Plan

### Step 1: Bulk Seed
- **Tool:** `scale_listings_50k.py`
- **Method:** `COPY` or `INSERT` in chunks (avoiding ORM overhead).
- **Validation:** Check `count(*)` and integrity constraints.

### Step 2: Search Path Load Test
- **Endpoint:** `/api/v2/search`
- **Scenario:** 
  - 100 concurrent users.
  - 50% Category Browse (Cached plan).
  - 30% Filtered Search (Complex predicates).
  - 20% Text Search.
- **Metric:** P95 < 150ms.

### Step 3: Detail Path Load Test
- **Endpoint:** `/api/v2/listings/{id}`
- **Scenario:** 
  - Random ID access (Cache miss simulation).
  - Related listings subquery stress.
- **Metric:** P95 < 120ms.

### Step 4: Soak Test
- **Duration:** 2 Hours steady load.
- **Focus:** Memory leaks, Connection pool exhaustion.

---

## 4. Success Criteria (Gate)
- [ ] Database size fits comfortably in memory (Buffer Hit Ratio > 99%).
- [ ] No Sequential Scans on critical paths.
- [ ] API Error Rate < 0.1%.
- [ ] P95 Latency targets met.
