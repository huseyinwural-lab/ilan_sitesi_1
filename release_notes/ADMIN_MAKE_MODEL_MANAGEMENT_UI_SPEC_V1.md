# Admin Make/Model Management UI Spec v1

**User:** Super Admin / Content Manager

## 1. Screens
### A. Make List (`/admin/vehicles/makes`)
-   **Table:** Logo, Name, Type (Car/Moto), Active Status, Model Count.
-   **Actions:** Edit, Toggle Active.
-   **Search:** By Name.

### B. Model List (`/admin/vehicles/makes/{id}/models`)
-   **Context:** Models of "BMW".
-   **Table:** Name, Years, Type.
-   **Actions:** Edit, Merge (Advanced).

### C. Merge Tool
-   **Scenario:** "3-Series" and "3 Series" both exist.
-   **UI:** Select Source -> Select Target -> "Merge".
-   **Backend:** Updates all Listings to Target ID -> Deletes Source.

## 2. i18n
-   **Labels:** Allow overriding Name for TR/DE/FR if market specific (e.g. Opel vs Vauxhall).
