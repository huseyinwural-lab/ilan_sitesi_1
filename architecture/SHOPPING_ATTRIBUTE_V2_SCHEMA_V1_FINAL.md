# Shopping Attribute v2 Schema v1 Final

**Approach:** Typed EAV (Entity-Attribute-Value) Table

## 1. Table: `listing_attributes`
To support high-performance filtering without JSONB bloat for critical specs.

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `listing_id` | UUID | FK `listings` |
| `attribute_id` | UUID | FK `attributes` |
| `value_text` | String | For text inputs |
| `value_number` | Numeric | For specs (GB, Inch) |
| `value_boolean` | Boolean | For flags |
| `value_option_id`| UUID | FK `attribute_options` (Selects) |

## 2. Attribute Types
-   **Select:** Uses `value_option_id`.
-   **Multi-Select:** Multiple rows with same `listing_id` + `attribute_id`.
-   **Number:** Uses `value_number`.
-   **Boolean:** Uses `value_boolean`.

## 3. Variant Logic (`is_variant`)
-   Attributes like `Size` and `Color` in Fashion are flagged `is_variant=True`.
-   These are critical for "Facets" in Search.

## 4. Category Binding
-   Reuses existing `category_attribute_map` table.
-   Logic: "If Category X is selected, show Attributes Y, Z".
