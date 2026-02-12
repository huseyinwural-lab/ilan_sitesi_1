# Real Estate Global Attributes v1

**Scope:** Applied to ALL Real Estate Categories (Housing, Commercial, Land).

## 1. Attributes

### 📐 Area (Alan)
-   **Key:** `m2_gross`
    -   **Type:** Number (Integer)
    -   **Unit:** m²
    -   **Validation:** Min 0, Max 1,000,000
    -   **Filter:** Range (Min - Max)
    -   **Mandatory:** **YES**
-   **Key:** `m2_net`
    -   **Type:** Number (Integer)
    -   **Unit:** m²
    -   **Validation:** Min 0, Max <= m2_gross
    -   **Filter:** Range (Min - Max)
    -   **Mandatory:** **YES**

### 🏗 Structure (Yapı)
-   **Key:** `building_status`
    -   **Type:** Select (Single selection in Form, Multi in Filter)
    -   **Options:** *See Translation Doc*
    -   **Filter:** Multi-Select
-   **Key:** `heating_type`
    -   **Type:** Select
    -   **Options:** *See Translation Doc*
    -   **Filter:** Multi-Select

### 💰 Financial (Finansal)
-   **Key:** `eligible_for_bank`
    -   **Type:** Boolean
    -   **Label:** Krediye Uygunluk
    -   **Filter:** Checkbox ("Show only eligible")
-   **Key:** `swap_available`
    -   **Type:** Boolean
    -   **Label:** Takaslı
    -   **Filter:** Checkbox
-   **Key:** `dues`
    -   **Type:** Number
    -   **Label:** Aidat (Monthly Fee)
    -   **Unit:** Currency (EUR/TRY/CHF)
    -   **Filter:** Range
