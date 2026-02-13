# P9 Cache Invalidation Policy

**Document ID:** P9_CACHE_INVALIDATION_POLICY_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Strategy: Soft TTL + Lazy Expiry
Due to the high cardinality of search combinations, "Purge All" on every listing update is too expensive.

### 1.1. Listing Updates (Create/Update/Delete)
- **Action:** Do NOT purge search cache immediately.
- **Reliance:** Rely on the short TTL (60s) for search results to naturally expire.
- **Rationale:** A 1-minute delay in a new listing appearing in search results is acceptable for Beta.
- **Detail Page:** MUST purge `listing:v2:{uuid}` immediately.

### 1.2. Master Data Updates (Attributes/Categories)
- **Action:** Purge relevant keys if possible, but given low frequency, manual cache flush or TTL is fine.

## 2. Implementation
For P9, we stick to **Time-based Expiry (TTL)** as the primary mechanism for Search Results to avoid complex invalidation logic bugs.

**Rule:** `TTL = 60 seconds` for all `search:v2:*` keys.
