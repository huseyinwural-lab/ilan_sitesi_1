# Real Estate Listing Attribute Templates v1

**Logic:** Dynamic Attribute Generation based on Category Type.

## 1. Template: Residential Sale (Konut Satılık)
-   **Global:**
    -   `m2_gross`: 50 - 300
    -   `m2_net`: `m2_gross` * 0.85
    -   `building_status`: Random(new, used, construction)
    -   `heating_type`: Random(combi_gas, central, floor)
-   **Residential:**
    -   `room_count`: Weighted Random (2+1: 40%, 3+1: 30%, 1+1: 20%, 4+1: 10%)
    -   `floor_location`: Random(ground, 1, 2, 3, 4, 5-10)
    -   `bathroom_count`: 1 (if room<3), 2 (if room>=3)
    -   `balcony`: True (80%)
    -   `in_complex`: True (40%)

## 2. Template: Residential Rent (Konut Kiralık)
-   **Inherits:** Residential Sale rules.
-   **Overrides:**
    -   `furnished`: True (30%)
    -   `dues` (Aidat): Random(50, 500) EUR

## 3. Template: Commercial (Ticari)
-   **Global:**
    -   `m2_gross`: 100 - 2000
    -   `m2_net`: `m2_gross` * 0.9
-   **Commercial:**
    -   `ceiling_height`: Random(2.8, 6.0)
    -   `entrance_height`: Random(2.2, 4.5)
    -   `power_capacity`: Random(10, 150) kW
    -   `is_transfer` (Devren): True (20% if Rent)
    -   `ground_survey`: Random(done, not_done)
