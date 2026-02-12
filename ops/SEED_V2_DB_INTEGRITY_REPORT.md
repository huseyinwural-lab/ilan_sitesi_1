# Seed v2 DB Integrity Report

**Target:** Integrity Validation

## 1. Uniqueness
-   Attribute Key must be unique globally.
-   Option Value must be unique per Attribute.

## 2. Inheritance
-   `m2_gross` linked to Root `real_estate` -> Inherited by `housing` -> Inherited by `apartment-sale`.
-   `room_count` linked to `housing` -> Inherited by `apartment-sale`.
-   `ceiling_height` linked to `commercial` -> Inherited by `warehouse`.

## 3. Constraints
-   `attribute_type` must match ENUM (`text`, `number`, `select`, `boolean`).
-   `unit` allowed only for `number`.
