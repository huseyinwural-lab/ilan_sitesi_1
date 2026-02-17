# P27: Reputation System Schema (V1)

## 1. Objective
To build a trusted marketplace where buyers and sellers can rate each other based on actual interactions.

## 2. Database Schema

### 2.1. Table: `user_reviews`
Stores individual ratings and comments.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `reviewer_id` | UUID | User giving the rating (FK -> users) |
| `reviewed_user_id` | UUID | User receiving the rating (FK -> users) |
| `listing_id` | UUID | Context of the review (FK -> listings) |
| `rating` | Integer | 1 to 5 stars |
| `comment` | Text | Optional feedback |
| `status` | String | `active`, `moderated`, `deleted` |
| `created_at` | DateTime | - |

**Constraints**:
*   `UniqueConstraint('reviewer_id', 'listing_id')`: One review per interaction.
*   **Validation**: User can only review if a `Conversation` exists between them for that `listing_id`.

### 2.2. User Profile Enrichment (Denormalization)
To avoid `AVG()` queries on every profile load, we add columns to `users` table:
*   `rating_avg`: Float (e.g., 4.8)
*   `rating_count`: Integer (e.g., 150)
*   `trust_score`: Float (Internal score 0-100 based on KYC + Reviews)

## 3. Calculation Logic
*   **On Insert Review**:
    1.  Calculate new average: `(old_avg * old_count + new_rating) / (old_count + 1)`
    2.  Increment count.
    3.  Update `users` table.

## 4. API Endpoints
*   `POST /reviews`: Submit a review.
*   `GET /users/{id}/reviews`: List reviews for a user.
