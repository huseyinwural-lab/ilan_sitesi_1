# Shopping Vertical Domain Model v1

**Goal:** Flexible attribute system for diverse product types.

## 1. Category Tree (Top Level)
1.  **Electronics (Elektronik)**
    -   Smartphones, Computers, TV/Audio, Cameras.
2.  **Home & Garden (Ev & Yaşam)**
    -   Furniture, Decoration, White Goods (Beyaz Eşya), Garden.
3.  **Fashion (Moda)**
    -   Clothing, Shoes, Accessories.
4.  **Hobbies (Hobi)**
    -   Sports, Music, Art.

## 2. Entity Map
-   **Listing:** Standard `listings` table.
-   **Attributes:** JSONB `attributes` (Dynamic).
-   **Master Data:** 
    -   **Brands:** `shopping_brands` table (Optional - *Decision needed*).
    -   *Decision:* For MVP, use `AttributeOption` for Brands (like old vehicle model) or simple text? 
    -   *Strategy:* Electronics needs Structured Brands (Apple, Samsung). Fashion needs too many. 
    -   *Verdict:* Use `Attribute` type `select` with curated Options for Electronics. Use `text` for others.

## 3. Key Relationships
-   `Electronics` -> Requires `brand`, `model`, `condition`, `warranty`.
-   `Fashion` -> Requires `size`, `color`, `condition`, `brand` (text).
