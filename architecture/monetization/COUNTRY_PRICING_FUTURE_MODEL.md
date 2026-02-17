# Country Pricing Future Model

## 1. Requirement
Different purchasing power and market rates per country.

## 2. Model (`price_configs`)
*   `country_code`: DE, TR...
*   `product_type`: listing, boost, showcase...
*   `price`: Decimal
*   `currency`: EUR, TRY...

## 3. Current State (MC1)
*   **Table**: Exists (P1).
*   **Seed**: All set to €0 or disabled via Feature Flag.
