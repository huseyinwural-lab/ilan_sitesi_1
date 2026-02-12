# Live Category Tree & Attributes (v1)

**Target Market:** Germany (DE) + Global Fallback
**Languages:** EN (Base), DE, TR

## 1. Real Estate (Emlak)
**Module:** `real_estate`

### A. Housing (Konut)
*   **Attributes:**
    *   `m2` (Number, Unit: m²) - Required, Filterable
    *   `room_count` (Select: 1, 1.5, 2, 2.5, 3, 4, 5+) - Required, Filterable
    *   `floor` (Number)
    *   `heating_type` (Select: Gas, Electric, Central, Heat Pump)
*   **Subcategories:**
    1.  **Apartment for Sale** (Wohnung kaufen)
    2.  **Apartment for Rent** (Mietwohnung)
    3.  **House for Sale** (Haus kaufen)
    4.  **House for Rent** (Haus mieten)

### B. Commercial (İşyeri)
*   **Attributes:**
    *   `m2` (Number)
    *   `commercial_type` (Select: Office, Shop, Warehouse, Hotel)
*   **Subcategories:**
    1.  **Office & Praxis** (Büro & Praxis)
    2.  **Retail & Trade** (Einzelhandel)
    3.  **Warehouse & Production** (Halle & Produktion)

---

## 2. Vehicles (Vasıta)
**Module:** `vehicle`

### A. Cars (Otomobil)
*   **Attributes:**
    *   `brand` (Select: BMW, Mercedes, VW, Audi, Tesla...) - Required, Filterable
    *   `model` (Text/Select) - Required
    *   `year` (Number) - Required, Filterable
    *   `km` (Number, Unit: km) - Required, Filterable
    *   `fuel_type` (Select: Petrol, Diesel, Hybrid, Electric)
    *   `gear_type` (Select: Manual, Automatic)
*   **Subcategories:**
    1.  **Used Cars** (Gebrauchtwagen)
    2.  **New Cars** (Neuwagen)

### B. Motorcycles (Motosiklet)
*   **Attributes:**
    *   `brand` (Select: Yamaha, Honda, Kawasaki, Ducati...)
    *   `cc` (Number, Unit: cm³)
*   **Subcategories:**
    1.  **Motorcycles** (Motorräder)
    2.  **Scooters** (Roller)

---

## 3. Shopping / Second Hand (İkinci El)
**Module:** `shopping`

### A. Electronics
*   **Subcategories:**
    1.  **Smartphones** (Handys & Smartphones) -> Attr: `brand`, `storage`
    2.  **Computers** (Computer & Zubehör) -> Attr: `processor`, `ram`
    3.  **TV & Audio** (TV & Video)

### B. Home & Garden
*   **Subcategories:**
    1.  **Furniture** (Möbel)
    2.  **Kitchen** (Küche)
    3.  **Garden** (Garten)

---

## 4. Services (Hizmetler)
**Module:** `services`

### A. Professional
*   **Subcategories:**
    1.  **Tutoring** (Nachhilfe)
    2.  **Moving & Transport** (Umzug & Transport)
    3.  **Craftsmen** (Handwerker)

## 5. Seed Strategy
1.  **Clear Old Data:** Wipe existing `categories` and `attributes` tables to prevent duplicates.
2.  **Create Attributes:** Insert `Attribute` definitions first.
3.  **Create Categories:** Insert Hierarchy (Root -> Sub).
4.  **Link:** Create `CategoryAttributeMap` entries.
