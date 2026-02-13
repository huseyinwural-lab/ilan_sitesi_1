# Vehicle Master Data Schema v1

**Database:** PostgreSQL

## 1. Tables

### `vehicle_makes`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `name` | String | Unique, Not Null | Global Name (e.g. "BMW") |
| `slug` | String | Unique, Index | Normalized (e.g. "bmw") |
| `is_active` | Bool | Default True | Soft delete flag |
| `logo_url` | String | Nullable | Brand Logo |
| `vehicle_type` | Enum | Index | `car`, `moto`, `comm` (Array allowed?) -> *Decision: Array or separate rows?* -> **Separate rows** or generic. Let's use `vehicle_types` Array (e.g. BMW makes Cars and Motos). |

### `vehicle_models`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `make_id` | UUID | FK `vehicle_makes` | Parent Brand |
| `name` | String | Not Null | e.g. "3 Series", "Golf" |
| `slug` | String | Index | e.g. "3-series" |
| `year_start` | Int | Nullable | Production Start |
| `year_end` | Int | Nullable | Production End |
| `vehicle_type` | Enum | Not Null | `car`, `moto`, `comm` |
| `is_active` | Bool | Default True | |

## 2. Integrity Rules
-   **No Orphans:** Deleting a Make cascades to Models (or restricted). *Decision: Restricted.*
-   **Uniqueness:** `(make_id, slug)` tuple must be unique.
