# P22: ML Training Pipeline Specification

## 1. Objective
To build a supervised learning pipeline that predicts the probability of a user converting (Contact/Favorite) on a given listing.

## 2. Dataset Definition

### 2.1. Sources
*   **Interactions**: `user_interactions` table (The "Events").
*   **User State**: `user_features` table (The "Context" at time T, or latest snapshot).
*   **Item State**: `listings` table.

### 2.2. Labeling Logic (Target Y)
We treat this as a **Binary Classification** problem (Pointwise LTR).

| Label | Value | Definition |
| :--- | :--- | :--- |
| **Positive** | `1` | Event is `listing_contact_clicked` OR `listing_favorited`. |
| **Negative** | `0` | Event is `listing_viewed` AND no positive action taken within session. |

*Note: For V1, we simply treat every view without an action as a negative sample.*

### 2.3. Feature Engineering (X)

#### User Features (Context)
*   `user_activity_score`: Float (from Feature Store).
*   `cat_affinity_{category_id}`: Float (Sparse vector).
*   `device_type`: Categorical (encoded).

#### Item Features (Content)
*   `price_log`: Log(Price).
*   `is_premium`: Boolean.
*   `recency_hours`: Hours since published.
*   `image_count`: Integer.

## 3. Pipeline Steps (`extract_training_data.py`)
1.  **Windowing**: Select interactions from last 90 days.
2.  **Joining**: Join Interaction -> Listing -> UserFeature.
3.  **Transformation**: Normalize numericals, encode categoricals.
4.  **Export**: Save as `training_set_{date}.csv` or Parquet.

## 4. Evaluation Metrics
We simulate a ranking task by grouping predictions by `user_id`.
*   **Precision@10**: % of relevant items in top 10.
*   **NDCG@10**: Ranking quality measure.
