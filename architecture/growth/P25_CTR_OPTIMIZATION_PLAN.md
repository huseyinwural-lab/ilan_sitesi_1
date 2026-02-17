# P25: Search -> Detail CTR Optimization Plan

## 1. Hypothesis
Users are seeing results but not clicking because the "Card" lacks key information or urgency.

## 2. Card Design Tweaks (A/B Test)
*   **Variant A (Control)**: Standard Card (Image, Price, Title).
*   **Variant B (Information Density)**: Add "3 days ago", "Verified Seller" icon, "Low Price" badge (if price < market avg).
*   **Variant C (Visual Focus)**: Larger Image (Aspect 3:2), Smaller Title.

## 3. Premium Highlight
*   **Current**: Gold Border.
*   **Optimized**: Add "Featured" label on top-left of image. Subtle background color (`bg-yellow-50`).

## 4. Implementation
*   Frontend: `SearchCard.js` handles variants via prop.
*   Backend: `SearchService` returns `market_price_comparison` flag.
