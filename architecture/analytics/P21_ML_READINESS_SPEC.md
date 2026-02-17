# P21: ML Readiness & Feature Store Specification

## 1. Objective
To prepare the system for Phase 2 AI implementation by establishing a **Feature Store** and **Batch Aggregation Pipeline**. This moves us from real-time query calculation (expensive) to pre-computed vectors (fast).

## 2. Feature Store Schema (`user_features`)
This table serves as the "Online Feature Store" for serving recommendations and the "Offline Feature Store" snapshot source for training.

| Column | Type | Description |
| :--- | :--- | :--- |
| `user_id` | UUID (PK) | Unique User Identifier |
| `category_affinity` | JSONB | Vector: `{"cat_id": score, ...}` |
| `city_affinity` | JSONB | Vector: `{"berlin": score, ...}` |
| `price_sensitivity` | Float | 0.0 (Budget) to 1.0 (Premium) |
| `activity_score` | Float | Derived from frequency/recency |
| `last_updated_at` | DateTime | Timestamp of last aggregation |

## 3. Batch Aggregation Strategy
**Job:** `daily_feature_update.py`
*   **Frequency:** Daily (at 03:00 UTC).
*   **Logic:**
    1.  Fetch `UserInteraction` for last 90 days.
    2.  Apply decay function (Linear or Exponential).
    3.  Aggregate scores per User -> Category/City.
    4.  Upsert into `user_features`.

## 4. Model Training Readiness

### 4.1. Problem Definition
*   **Goal:** Predict probability of `Contact` (Lead) given `User` and `Listing`.
*   **Type:** Binary Classification (CTR / CVR).

### 4.2. Input Features (X)
*   **User:** `category_affinity`, `city_affinity`, `price_sensitivity`.
*   **Item:** `category_id`, `city`, `price`, `is_premium`, `image_count`.
*   **Context:** `day_of_week`, `hour_of_day`, `device_type`.

### 4.3. Target Label (Y)
*   **Positive (1):** `listing_contact_clicked` OR `listing_favorited`.
*   **Negative (0):** `listing_viewed` (without action) OR `impression` (if available).

## 5. Next Steps (Phase 2)
1.  Collect 10k+ interaction events.
2.  Export training dataset (Parquet).
3.  Train XGBoost / LightGBM ranker.
4.  Deploy model as microservice.
