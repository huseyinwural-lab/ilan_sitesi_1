# Attribute Validation Matrix

**Enforcement:** Backend `ListingService` + Frontend Form Validation.

| Category Scope | Attribute Key | Requirement |
| :--- | :--- | :--- |
| **All Real Estate** | `m2_gross` | **Mandatory** |
| **All Real Estate** | `m2_net` | **Mandatory** |
| **Residential (Sale/Rent)** | `room_count` | **Mandatory** |
| **Residential** | `heating_type` | Optional |
| **Residential** | `floor_location` | Optional |
| **Commercial** | `is_transfer` | Optional |
| **Land (Arsa)** | *ALL above* | **N/A (Out of Scope)** |

## Rules
1.  **Konut:** Must have `room_count`.
2.  **Ticari:** No strict mandatory fields beyond Global `m2`, but `is_transfer` is highly recommended for Rent.
3.  **Validation Failure:** Returns `422 Unprocessable Entity` with `detail: "Missing mandatory attribute: room_count"`.
