# P21: Event Taxonomy V2.0

## 1. Objective
To capture granular user behavioral data to power the Recommendation Engine (P21) and Advanced Analytics.

## 2. Event Types (`event_type`)

### 2.1. Listing Interaction
| Event Type | Description | Weight (Affinity) |
| :--- | :--- | :--- |
| `listing_viewed` | User views a listing detail page. | 1 |
| `listing_favorited` | User adds listing to favorites. | 5 |
| `listing_contact_clicked` | User clicks "Call" or "Message". | 10 |
| `listing_shared` | User shares the listing. | 3 |

### 2.2. Discovery Interaction
| Event Type | Description | Weight |
| :--- | :--- | :--- |
| `search_performed` | User performs a keyword search. | N/A (Context) |
| `category_browsed` | User opens a category page. | 0.5 |
| `filter_applied` | User applies price/city filters. | N/A (Context) |

## 3. Metadata Schema (`metadata` JSONB)

### 3.1. Standard Fields (Columns)
To ensure query performance, these core dimensions are First-Class Columns in DB:
- `listing_id` (UUID)
- `category_id` (UUID)
- `city` (String) - *Note: Using string as City ID is not yet standard*
- `country_code` (String)

### 3.2. Context Fields (JSONB)
- `device_type`: 'mobile', 'web', 'tablet'
- `source`: 'home_feed', 'search_result', 'related_items'
- `search_query`: (For `search_performed`)
- `price_range`: (For `filter_applied`)

## 4. Indexing Strategy
To support real-time aggregation for "Recently Viewed" and "User Affinity":
1.  **Time-Series**: `(event_type, created_at DESC)` -> Fast filtering of recent events.
2.  **User Profile**: `(user_id, event_type, created_at DESC)` -> Fast retrieval of user history.
3.  **Item Popularity**: `(listing_id, event_type)` -> Counting views/likes per item.

## 5. Data Retention
- **Hot Data (DB)**: 90 Days.
- **Cold Data (Archive)**: Dump to S3/Parquet after 90 days.
