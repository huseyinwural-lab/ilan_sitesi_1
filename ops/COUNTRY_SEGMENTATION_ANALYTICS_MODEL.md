# Country Segmentation Analytics Model

## 1. Metric Dimensions
All key metrics MUST be grouped by `country_code`.

### 1.1. Supply (Listings)
*   **Active Listings**: `SELECT country, COUNT(*) FROM listings WHERE status='active' GROUP BY country`
*   **New Listings (24h)**: Growth velocity per market.

### 1.2. Demand (Users)
*   **DAU**: `SELECT country_code, COUNT(DISTINCT user_id) FROM user_interactions GROUP BY country_code`
*   **Search Volume**: Count `search_performed` events.

## 2. Implementation
*   **Dashboard**: Admin Panel > Analytics > "Global Overview" vs "Country Detail".
*   **Storage**: `user_interactions` already has `country_code` (P21).
