# L2: Search CTR Analysis Plan

## 1. Metric: Click-Through Rate (CTR)
`CTR = Total Detail Views / Total Search Impressions`

## 2. Low CTR Diagnosis (< 5%)
If users search but don't click:
*   **Price**: Are list prices too high?
*   **Image**: Are thumbnails blurry or placeholders?
*   **Title**: Is the info relevant?

## 3. A/B Tests (List View)
*   **Thumbnail Size**: Larger vs Smaller cards.
*   **Price Visibility**: Highlight Price vs Highlight Location.
*   **Badges**: "New" vs "Verified" badge priority.

## 4. Action
*   Analyze query logs for "pogo-sticking" (Click -> Back immediately).
*   Adjust `ML Ranking` weights to punish low-CTR items.
