# Vehicle Master Data Schema v1 Final

**Database:** PostgreSQL

## 1. Table: `vehicle_makes`
| Column | Type | Constraint | Note |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `slug` | String(100) | Unique, Index | e.g. "mercedes-benz" |
| `name` | String(100) | Not Null | Display Name |
| `vehicle_types` | Array[String] | | ['car', 'comm'] |
| `is_active` | Bool | Default True | |
| `source` | String(50) | | "manual", "provider_x" |
| `source_ref` | String(100) | | External ID |
| `updated_at` | DateTime | | |

## 2. Table: `vehicle_models`
| Column | Type | Constraint | Note |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | |
| `make_id` | UUID | FK `vehicle_makes` | |
| `slug` | String(100) | Index | e.g. "c-class" |
| `name` | String(100) | Not Null | |
| `vehicle_type` | String(20) | Not Null | |
| `year_from` | Int | Nullable | |
| `year_to` | Int | Nullable | |
| `is_active` | Bool | Default True | |

## 3. Constraints
-   Unique Constraint: `(make_id, slug)` on `vehicle_models`.
