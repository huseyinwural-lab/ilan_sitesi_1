# Vehicle Attributes UI Smoke v1

**Env:** Staging

## 1. Car Form
-   [ ] **Fuel Type:** Dropdown (Benzin, Diesel...).
-   [ ] **Emission:** Dropdown (Euro 6...).
-   [ ] **Power:** Input (kW). Label should clarify kW.

## 2. Moto Form
-   [ ] **Type:** Dropdown (Scooter...).
-   [ ] **ABS:** Checkbox.
-   [ ] **Fuel Type:** NOT visible (Inherited? No, Fuel is Car specific in this design? Wait, Moto needs fuel too. Let's make Fuel GLOBAL or duplicate? *Decision: Make Fuel Global or duplicate logic in script. For v4, Fuel is defined in Cars. Moto usually has Fuel too. We should bind `fuel_type` to Moto too.* -> **Update Plan: Bind `fuel_type` to Moto as well.**)

## 3. Commercial Form
-   [ ] **Payload:** Input (kg).
-   [ ] **Box Type:** Dropdown.
