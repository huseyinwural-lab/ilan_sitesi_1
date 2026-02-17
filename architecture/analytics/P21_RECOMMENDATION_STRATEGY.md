# P21: Recommendation Strategy (V1)

## 1. Objective
To provide personalized listing recommendations to users to increase engagement (CTR) and conversion (Contact/Lead).

## 2. Hybrid Model Approach
For V1, we use a Rule-Based Hybrid Model combining **User Affinity** and **Global Popularity**.

### 2.1. Signal Weights (Affinity Scoring)
We calculate a score for each `Category` and `City` based on user interactions in the last 30 days.

| Event Type | Weight | Decay (Half-Life) |
| :--- | :--- | :--- |
| `listing_viewed` | 1 | 7 Days |
| `listing_favorited` | 5 | 14 Days |
| `listing_contact_clicked` | 10 | 30 Days |
| `search_performed` | 2 | 3 Days |

**Formula**:
`Affinity(Category A) = Σ (Event_Weight * Time_Decay_Factor)`

### 2.2. Candidate Generation Strategy
1.  **Personalized Candidates (80%)**:
    *   Identify Top 3 Affinity Categories.
    *   Identify Top 2 Affinity Cities.
    *   Query: `SELECT * FROM listings WHERE category IN (Top3) AND city IN (Top2) ORDER BY is_premium DESC, created_at DESC`.
2.  **Cold-Start / Popular Candidates (20%)**:
    *   If user has no history or few results.
    *   Query: `SELECT * FROM listings WHERE country = user_country ORDER BY view_count DESC, is_premium DESC`.

## 3. Cold-Start Problem
*   **New User**: Show "Trending in {Country}".
*   **New Item**: Boost new items slightly in feed (Recency Bonus).

## 4. API Contract
`GET /api/v2/mobile/recommendations`
*   **Response**: Same `MobileListingCard` DTO as Feed.
*   **Limit**: 10 items (Horizontal scroll widget).
