# P10 Premium Sorting Integration

**Document ID:** P10_PREMIUM_SORTING_INTEGRATION_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Objective
Monetize search visibility by allowing users to purchase "Showcase" or "Bump" status, affecting the sorting order of the Search API v2.

## 2. Sorting Logic

### 2.1. Default Sort (Relevance/Date)
Standard: `ORDER BY created_at DESC`

### 2.2. Premium Boosted Sort
Revised: `ORDER BY is_showcase DESC, created_at DESC`

**Behavior:**
- All "Showcase" items appear at the top.
- Within Showcase items, sort by Date.
- Within Standard items, sort by Date.

### 2.3. "Bump" (Üste Taşı)
- **Logic:** Does NOT use a separate boolean flag.
- **Action:** Updates `created_at` timestamp to `NOW()`.
- **Effect:** Listing naturally moves to top of its segment (Showcase or Standard).

---

## 3. Implementation Plan

### 3.1. Database
- Add `is_showcase` boolean column to `listings` (and index it!).
- Update `ix_listings_cat_status_price` -> `ix_listings_cat_status_showcase_price`.

### 3.2. Search API
- Update `search_routes.py` sorting logic.
- **Risk:** Index usage. `ORDER BY is_showcase DESC, created_at DESC` requires composite index `(category_id, status, is_showcase, created_at)`.

### 3.3. Expiry
- Worker Job: `check_premium_expiry`.
- Action: Set `is_showcase = False` when time is up.

---

## 4. Abuse Prevention
- **Bump Rate Limit:** Max 1 bump every 24 hours per listing.
- **Showcase Saturation:** Limit 5 showcase items per page? (No, allow unlimited if paid, pagination handles it).
