# Search & Filter Logic v1

**Goal:** Standardize how attribute types map to Frontend Filter Components.

## 1. Number Types (Integer/Float)
-   **Logic:** Range Filter.
-   **UI:** Two inputs: `Min` and `Max`.
-   **Example:** `m2_gross`, `price`, `dues`, `ceiling_height`.
-   **Backend:** `WHERE attr ->> 'm2_gross' >= min AND attr ->> 'm2_gross' <= max`.

## 2. Select Types (Enum)
-   **Logic:** Multi-Select OR logic.
-   **UI:** Checkbox list or Multi-select dropdown.
-   **Example:** `room_count`, `heating_type`, `building_status`.
-   **Behavior:** Selecting "2+1" AND "3+1" means show listings that match *EITHER*.
-   **Backend:** `WHERE attr ->> 'room_count' IN ('2+1', '3+1')`.

## 3. Boolean Types
-   **Logic:** "Only True" Toggle.
-   **UI:** Single Checkbox.
-   **Example:** `furnished`, `balcony`, `is_transfer`.
-   **Behavior:**
    -   Unchecked: Show All (True + False).
    -   Checked: Show Only True.
-   **Backend:** `IF checked: WHERE attr ->> 'furnished' = 'true'`.

## 4. Special Cases
-   **Floor:** Currently treated as Select (Enum) for simplicity in aggregation, though it represents height.
