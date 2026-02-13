# Shopping Domain Model v1 Final

**Status:** LOCKED
**Module:** Shopping

## 1. Category Taxonomy
### A. Electronics (Elektronik)
-   **Smartphones** (Cep Telefonu)
-   **Computers** (Bilgisayar) -> Laptops, Desktops, Tablets.
-   **TV & Audio** (TV & Ses) -> Televisions, Headphones, Speakers.
-   **Cameras** (Kamera)

### B. Home & Living (Ev & Yaşam)
-   **Furniture** (Mobilya) -> Sofa, Bed, Table.
-   **Decoration** (Dekorasyon)
-   **White Goods** (Beyaz Eşya) -> Fridge, Washing Machine.
-   **Garden** (Bahçe)

### C. Fashion (Moda)
-   **Clothing** (Giyim) -> Men, Women, Kids.
-   **Shoes** (Ayakkabı)
-   **Accessories** (Aksesuar)

### D. Hobbies (Hobi)
-   **Sports** (Spor)
-   **Music** (Müzik)
-   **Art** (Sanat)

## 2. Listing Types
-   **Standard:** Single item (e.g. A used phone).
-   **Variant:** Multi-sku (e.g. A T-Shirt available in S, M, L).
    -   *MVP Strategy:* Each variant is a separate listing OR linked via `group_id`.
    -   *Decision:* For MVP, treat variants as Attribute Selection on Listing (if quantity > 1) or Separate Listings.
    -   *Simplification:* Treat as Separate Listings for Search efficiency.

## 3. Localization Strategy
-   **Labels:** All Categories and Attributes have TR/DE/FR keys.
-   **Values:** Enum options (Red/Kırmızı) are localized.
-   **User Input:** Title/Desc entered in Seller's language, auto-translation (future) or displayed as is.
