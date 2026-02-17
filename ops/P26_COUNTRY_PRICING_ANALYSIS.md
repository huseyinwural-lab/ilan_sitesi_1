# P26: Country Pricing Analysis

## 1. Purchasing Power Parity (PPP) Adjustment
We cannot charge €49 in TR if we charge €49 in DE.

### 1.1. Multipliers (Base: DE)
*   **DE (Germany)**: 1.0 (Ref) -> €49
*   **AT (Austria)**: 1.0 -> €49
*   **CH (Switzerland)**: 1.4 -> CHF 79 (~€80)
*   **TR (Turkey)**: 0.2 -> TRY 999 (~€30)

## 2. Config Implementation
*   Update `DealerPackage` model or `price_configs` to support per-country overrides.
*   **Decision**: Use `SystemConfig` for multipliers `pricing_ppp_multipliers = {"TR": 0.2, "CH": 1.4}`.
