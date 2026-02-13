# Pagination Determinism Policy v1

**Problem:** `ORDER BY price` is unstable if prices are equal.
**Solution:** Always append `id` or `created_at` as tie-breaker.

## 1. Rules
-   **Default:** `ORDER BY created_at DESC, id DESC`.
-   **Price Sort:** `ORDER BY price ASC, id DESC`.
-   **Relevance:** `ORDER BY rank DESC, id DESC`.

## 2. Enforcement
-   **Code Review:** Check all `order_by` clauses in `search_routes.py`.
-   **Test:** Create 20 listings with same price. Page 1 and Page 2 must have 0 overlap.
