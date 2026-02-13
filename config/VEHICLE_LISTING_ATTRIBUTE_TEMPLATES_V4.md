# Vehicle Listing Attribute Templates v4

**Logic:** Dynamic Attribute Generation based on Category.

## 1. Template: Car (Otomobil)
-   **Global:**
    -   `year`: 2010 - 2025
    -   `km`: 0 - 250,000
    -   `condition`: used (80%), new (15%), damaged (5%)
-   **Specific:**
    -   `fuel_type`: Random(gasoline, diesel, hybrid, electric)
    -   `gear_type`: Random(manual, automatic)
    -   `body_type`: Random(sedan, suv, hatchback, station)
    -   `engine_power_kw`: 60 - 300
    -   `engine_capacity_cc`: 1000 - 3000
    -   `emission_class`: Euro 6 (60%), Euro 5 (30%), Euro 4 (10%)
    -   `inspection_valid`: True (80%)

## 2. Template: Moto (Motosiklet)
-   **Global:**
    -   `km`: 0 - 50,000
-   **Specific:**
    -   `moto_type`: Random(scooter, racing, chopper, naked)
    -   `abs`: True (70%)

## 3. Template: Commercial (Ticari)
-   **Global:**
    -   `km`: 50,000 - 500,000
-   **Specific:**
    -   `comm_vehicle_type`: Random(van, truck)
    -   `load_capacity_kg`: 1000 - 20000
    -   `box_type`: Random(closed, open, frigo)
