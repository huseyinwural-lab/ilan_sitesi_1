# P23: Query & Cost Optimization Report

## 1. Objective
Identify and optimize the most expensive database queries to reduce CPU load and enable scale.

## 2. Top Expensive Queries (Audit)

### 2.1. Landing Page (High Volume)
*   **Query**: `SELECT * FROM listings WHERE country = 'TR' AND city = 'istanbul' ORDER BY is_premium DESC, created_at DESC LIMIT 20`
*   **Issue**: Frequent execution on large dataset.
*   **Optimization**: Ensure composite index `(country, status, city, is_premium, created_at)` exists.

### 2.2. Recommendations (Complex)
*   **Query**: `SELECT * FROM listings WHERE id NOT IN (...) ORDER BY view_count DESC`
*   **Issue**: `NOT IN` with large lists is slow. `ORDER BY view_count` scans full table if not indexed.
*   **Optimization**: Index `(country, status, view_count DESC)`.

### 2.3. Analytics Aggregation (Batch)
*   **Query**: `SELECT * FROM user_interactions WHERE created_at > ...`
*   **Issue**: Table grows indefinitely.
*   **Optimization**: Partition table by month (Future work). For now, ensure index `(created_at)` is used.

## 3. Index Refinement Plan
We will apply the following indexes via migration:

1.  `ix_listings_feed_opt`: `(status, country, is_premium, created_at)` -> Covers Feed & Landing.
2.  `ix_listings_pop_opt`: `(status, country, view_count DESC)` -> Covers Popularity Fallback.
3.  `ix_interactions_date_opt`: `(event_type, created_at)` -> Covers Aggregation jobs.

## 4. Compute Optimization
*   **Batch Inference**: ML Service currently scores per-user.
    *   *Plan*: Move to Batch Scoring for "Home Feed" candidates every 1 hour, cache results in Redis. (Deferred to P24).
