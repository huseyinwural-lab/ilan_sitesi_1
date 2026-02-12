# Real Estate Residential Room Count EU Revision v1

**Goal:** Standardize room count to Total Rooms (European Standard) instead of TR-specific Salon+Room format.

## 1. Schema Change
-   **Old:** Enum Strings ("1+0", "1+1", "2+1"...)
-   **New:** Enum/Integer-like Strings ("1", "2", "3", "4", "5", "6+")

## 2. Options Mapping (Migration)
| Old Value | New Value | Label (EN/DE/TR/FR) | Sort Order |
| :--- | :--- | :--- | :--- |
| `1+0` | `1` | 1 Room / 1 Zimmer / 1 Oda / 1 Pièce | 1 |
| `1+1` | `2` | 2 Rooms / 2 Zimmer / 2 Oda / 2 Pièces | 2 |
| `2+1` | `3` | 3 Rooms / 3 Zimmer / 3 Oda / 3 Pièces | 3 |
| `2.5+1`| `3.5`| 3.5 Rooms / 3.5 Zimmer / 3.5 Oda / 3.5 Pièces | 4 |
| `3+1` | `4` | 4 Rooms / 4 Zimmer / 4 Oda / 4 Pièces | 5 |
| `3.5+1`| `4.5`| 4.5 Rooms / 4.5 Zimmer / 4.5 Oda / 4.5 Pièces | 6 |
| `4+1` | `5` | 5 Rooms / 5 Zimmer / 5 Oda / 5 Pièces | 7 |
| `4+2` | `6` | 6 Rooms / 6 Zimmer / 6 Oda / 6 Pièces | 8 |
| `5+1` | `6` | 6 Rooms / 6 Zimmer / 6 Oda / 6 Pièces | 8 |
| `5+2` | `7` | 7+ Rooms / 7+ Zimmer / 7+ Oda / 7+ Pièces | 9 |
| `6+` | `7` | 7+ Rooms / 7+ Zimmer / 7+ Oda / 7+ Pièces | 9 |

## 3. Implementation
-   Update `seed_production_data_v3.py` to upsert these new options.
-   Update `seed_real_estate_listings.py` to select from new range.
