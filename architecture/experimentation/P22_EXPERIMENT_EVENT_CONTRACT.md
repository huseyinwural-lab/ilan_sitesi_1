# P22: Experiment Event Contract

## 1. Objective
To track user exposure to A/B tests and attribute downstream conversions (clicks, subscriptions) to specific experiment variants.

## 2. Event Types

### 2.1. Exposure Event (`experiment_exposed`)
Triggered when a user is assigned to a group and views the treatment.
*   **Trigger**: `GET /recommendations` returns success.
*   **Storage**: `experiment_logs` table (High volume).

| Field | Type | Description |
| :--- | :--- | :--- |
| `experiment_name` | String | e.g., "revenue_boost_v1" |
| `variant` | String | "A" (Control) or "B" (Treatment) |
| `user_id` | UUID | The user exposed |
| `session_id` | String | For anonymous users (future proofing) |
| `device_type` | String | "mobile", "web" |
| `created_at` | DateTime | Timestamp |

### 2.2. Click Attribution (`recommendation_click`)
Triggered when a user clicks a recommended item.
*   **Trigger**: `GET /listing/{id}` with `source=recommendation`.
*   **Payload**:
    ```json
    {
      "event_type": "listing_viewed",
      "meta_data": {
        "source": "recommendation",
        "experiment_group": "B",
        "rank_position": 3
      }
    }
    ```

### 2.3. Conversion Binding
Revenue events must look back at recent exposures.
*   **Logic**: If User subscribes, check `experiment_logs` for last 7 days.
*   **Attribution Model**: Last-Touch (Last experiment seen wins).

## 3. Storage Schema (`experiment_logs`)
| Column | Type | Indexing |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `experiment_name` | String | Index |
| `variant` | String | - |
| `user_id` | UUID | Index |
| `created_at` | DateTime | Index (Partition key candidate) |

## 4. Analytics Queries
*   **CTR**: `Count(Clicks with Group B) / Count(Exposures Group B)`
*   **Significance**: Chi-Square test on the counts.
