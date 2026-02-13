# Shopping Attribute System v2

**Logic:** Inheritance & Polymorphism

## 1. Global Attributes (All Shopping)
-   **Condition:** New, Used, Refurbished.
-   **Price:** (Standard Listing Field).
-   **Delivery:** Shipping Available / Pickup Only.

## 2. Electronics (Attributes)
-   **Brand:** Select (Apple, Samsung, Sony...).
-   **Warranty:** Boolean.
-   **Specs:** 
    -   `storage_capacity` (128GB, 256GB...) - Select.
    -   `ram` (8GB, 16GB...) - Select.
    -   `screen_size` (Inch) - Number.

## 3. Fashion (Attributes)
-   **Size:** Select (S, M, L, XL, 38, 40...).
    -   *Challenge:* Size standards differ (EU vs US).
    -   *Solution:* Separate attributes `size_apparel` vs `size_shoes`.
-   **Color:** Select (Multi-color options).
-   **Gender:** Men, Women, Unisex, Kids.

## 4. Home (Attributes)
-   **Material:** Wood, Metal, Glass...
-   **Color:** Select.
