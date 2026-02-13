# Vehicle Cars Attributes v1

**Scope:** Automobiles (Otomobil) Sub-categories only.

## 1. Technical Specs
-   **Key:** `fuel_type`
    -   **Type:** Select
    -   **Mandatory:** **YES**
    -   **Filter:** Multi-Select (Petrol, Diesel, Electric, Hybrid).
-   **Key:** `gear_type`
    -   **Type:** Select
    -   **Mandatory:** **YES**
    -   **Filter:** Multi-Select (Manual, Automatic, Semi).
-   **Key:** `body_type`
    -   **Type:** Select
    -   **Filter:** Multi-Select (Sedan, SUV, Hatchback, Station, Coupe, Cabrio).
-   **Key:** `engine_power_kw`
    -   **Type:** Number
    -   **Unit:** kW
    -   **Filter:** Range.
    -   *Note:* UI converts to HP.
-   **Key:** `engine_capacity_cc`
    -   **Type:** Number
    -   **Unit:** cc
    -   **Filter:** Range.
-   **Key:** `drive_train`
    -   **Type:** Select
    -   **Options:** FWD, RWD, 4WD/AWD.

## 2. EU Regulations
-   **Key:** `emission_class`
    -   **Type:** Select
    -   **Options:** Euro 6, Euro 5, Euro 4...
    -   **Mandatory:** **YES (DE/FR)**, Optional (TR).
-   **Key:** `inspection_valid`
    -   **Type:** Boolean
    -   **Label:** TÜV / Inspection Valid.

## 3. Equipment (Simplified)
-   **Key:** `air_condition`
    -   **Type:** Select
    -   **Options:** None, Manual, Digital/Auto.
-   **Key:** `navigation` (Bool)
-   **Key:** `leather_seats` (Bool)
-   **Key:** `sunroof` (Bool)
-   **Key:** `parking_sensors` (Bool)
