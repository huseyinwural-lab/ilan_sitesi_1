# P25: City Liquidity Heatmap Report

## 1. Metric: Liquidity Score
`Score = Active Listings * (1 + Demand_Weight)`
*   **Active Listings**: Supply.
*   **Demand_Weight**: Normalized Search Volume (0.0 - 1.0).

## 2. Heatmap Categories
*   **Hot (Green)**: High Supply, High Demand (Berlin, Istanbul). **Action**: Monetize.
*   **Warm (Yellow)**: Low Supply, High Demand (Munich, Izmir). **Action**: Dealer Outreach.
*   **Cold (Blue)**: High Supply, Low Demand. **Action**: SEO / Paid Ads.
*   **Frozen (Gray)**: Low Supply, Low Demand. **Action**: Ignore / Noindex.

## 3. Implementation
*   **SQL View**: `city_liquidity_stats`.
*   **Dashboard**: Admin Map View.
