# Vehicle Moto Attributes v1

**Scope:** Motorcycles (Motosiklet).

## 1. Technical
-   **Key:** `moto_type`
    -   **Type:** Select
    -   **Options:** Scooter, Racing, Chopper, Cross, Touring, Naked.
-   **Key:** `engine_capacity_cc` (Inherited logic, shared key).
-   **Key:** `engine_power_hp`
    -   **Type:** Number
    -   **Unit:** hp
    -   *Note:* Moto world uses HP more than kW usually, but consistent kW is fine. Let's stick to `engine_power_kw` for consistency if possible, or use HP for Moto specific.
    -   *Decision:* Use `engine_power_kw` global key, UI shows HP.

## 2. Safety
-   **Key:** `abs`
    -   **Type:** Boolean
    -   **Label:** ABS.
