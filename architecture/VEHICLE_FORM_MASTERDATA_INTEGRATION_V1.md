# Vehicle Form MasterData Integration v1

**Goal:** Replace static dropdowns with Dynamic API calls.

## 1. Form Logic
1.  **Field:** `brand` (Select)
    -   **Source:** `GET /api/vehicles/makes?type=car`
    -   **Behavior:** On Change -> Reset `model`.
2.  **Field:** `model` (Select)
    -   **Source:** `GET /api/vehicles/models?make_id={selected_brand}`
    -   **State:** Disabled until Brand selected.

## 2. Filter Logic
-   **Sidebar:** Faceted Search.
-   **Behavior:** Multi-select Brand -> Models query searches `make_id IN (...)`.

## 3. SEO
-   **URLs:** `/de/fahrzeuge/autos/bmw/3er-reihe`
-   **Slug resolution:** URL slugs mapped to Master Data IDs.
