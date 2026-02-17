# Vehicle Domain Model v1

## 1. Master Data Tables
*   `vehicle_makes`: Audi, BMW, Mercedes.
*   `vehicle_models`: A3, 320i, C180. (Linked to Make).

## 2. Listing Attributes (JSONB)
Mapped via `Attribute` engine (U2.1).

| Key | Type | Example |
| :--- | :--- | :--- |
| `make_id` | Select | `uuid` |
| `model_id` | Select | `uuid` |
| `year` | Number | 2020 |
| `km` | Number | 50000 |
| `fuel_type` | Select | Diesel, Petrol, Electric |
| `transmission` | Select | Automatic, Manual |
| `body_type` | Select | Sedan, SUV, Hatchback |
| `color` | Select | Black, White |
| `engine_capacity`| Number | 1600 |
| `engine_power` | Number | 136 |

## 3. Validation Rules
*   `year`: 1900 - Current Year + 1.
*   `km`: >= 0.
