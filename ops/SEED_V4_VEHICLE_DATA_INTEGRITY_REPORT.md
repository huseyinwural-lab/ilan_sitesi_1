# Seed v4 Vehicle Data Integrity Report

**Status:** PENDING CHECK
**Target:** Seed v4 Output

## 1. Inheritance Logic
- [ ] `brand`, `model`, `year`, `km` linked to Root `vehicles` -> Inherited by `cars` and `motorcycles` and `commercial-vehicles`.

## 2. Segment Isolation
- [ ] **Cars:** Have `fuel_type`, `gear_type`, `emission_class`. Do NOT have `moto_type` or `load_capacity_kg`.
- [ ] **Moto:** Have `moto_type`, `abs`. Do NOT have `gear_type` (Car specific in this design) or `load_capacity_kg`.
-   *Correction:* Moto has gears but logic is different. Our v4 assigned `gear_type` to `cars` only. This is acceptable for v1 simplification.
- [ ] **Commercial:** Have `load_capacity_kg`, `comm_vehicle_type`. Do NOT have `moto_type`.

## 3. Localization
-   [ ] Verify `fuel_type`:
    -   Value `diesel`: "Diesel" (EN/DE/TR/FR).
-   [ ] Verify `body_type`:
    -   Value `sedan`: "Sedan" (EN/TR), "Limousine" (DE), "Berline" (FR).

## 4. Category Structure
-   [ ] `commercial-vehicles` exists and is child of `vehicles`.
