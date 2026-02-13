# Seed v6 Data Quality Rules

**Standard:** Provider-Grade (No "Lorem Ipsum").

## 1. Content Rules
-   **Titles:** Must follow `{Brand} {Model} {Key Spec}`.
    -   *Good:* "Apple iPhone 13 128GB Midnight"
    -   *Bad:* "Cheap Phone"
-   **Prices:** Must be realistic market value (+/- 20%).
    -   *Phone:* 300 - 1500 EUR.
    -   *Sofa:* 200 - 3000 EUR.

## 2. Completeness
-   **Electronics:** Brand, Model, Condition, Warranty MUST be filled.
-   **Fashion:** Size, Color, Condition MUST be filled.

## 3. Consistency
-   Global `condition` attribute used across all items.
-   `shipping_available` boolean populated for all.
