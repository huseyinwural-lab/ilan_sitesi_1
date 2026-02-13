# Soft Launch Configuration (Public Beta)

**Document ID:** SOFT_LAUNCH_CONFIGURATION_v1  
**Date:** 2026-02-13  
**Status:** ✅ ACTIVE  

---

## 1. Objective
Protect system stability during the initial "Soft Launch" phase by restricting traffic throughput and lowering alert thresholds. This compensates for the known Search API performance bottleneck (P95 ~870ms).

---

## 2. Configuration Changes

### 2.1. Rate Limiting (Backend)
**File:** `/app/backend/app/routers/search_routes.py`

| Endpoint | Old Limit | New Limit (Soft Launch) | Rationale |
|---|---|---|---|
| `GET /api/v2/search` | 100 req/min | **60 req/min** | Prevent DB CPU saturation due to expensive facet queries. |
| `GET /api/v2/listings/{id}` | N/A | **120 req/min** | Protect against scraping bots. |

### 2.2. Frontend Controls
- **Lazy Loading:** Ensure all listing images use `loading="lazy"` (Default in current UI).
- **Debounce:** Increase search input debounce from 300ms to **500ms** to reduce intermediate query load.

### 2.3. Monitoring Thresholds
Adjust observability alerts to trigger earlier.

| Metric | Normal Threshold | Soft Launch Threshold |
|---|---|---|
| **API Latency (P95)** | > 500ms | **> 1000ms** (Relaxed due to known issue) |
| **Error Rate** | > 1% | **> 0.5%** (Stricter) |
| **DB CPU** | > 80% | **> 60%** (Early warning) |

---

## 3. Rollout Plan
1. Apply Rate Limit change in `search_routes.py`.
2. Deploy backend service.
3. Verify headers (`X-RateLimit-Limit`) via curl.

---

## 4. Exit Criteria (End of Soft Launch)
- Search P95 optimized to < 200ms (P9 completion).
- No critical incidents for 48 hours.
- Redis caching implementation verified.
