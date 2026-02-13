# P7 Admin API MasterData Tickets v1

**Epic:** Admin Master Data Management
**Status:** OPEN

## Ticket 1: Attributes CRUD
-   **Endpoint:** `GET /attributes` (List with filter/sort)
-   **Endpoint:** `GET /attributes/{id}` (Detail)
-   **Endpoint:** `PATCH /attributes/{id}` (Update)
-   **Constraints:** `is_filterable`, `is_sortable`, `is_active` fields only. No deleting attributes.

## Ticket 2: Options CRUD
-   **Endpoint:** `GET /attributes/{id}/options` (List)
-   **Endpoint:** `PATCH /options/{id}` (Update labels, sort_order)
-   **Endpoint:** `POST /attributes/{id}/options` (Create new option for manual attributes)
-   **Constraints:** Prevent modifying provider-sourced option values.

## Ticket 3: Category Binding
-   **Endpoint:** `GET /categories/{id}/attributes` (List bound attributes)
-   **Endpoint:** `POST /categories/{id}/bind` (Super Admin Only)
-   **Endpoint:** `DELETE /categories/{id}/bind/{attr_id}` (Super Admin Only)

## Ticket 4: Audit & RBAC
-   **Middleware:** Ensure `ADMIN_UPDATE_MASTERDATA` log is written.
-   **Test:** Verify `country_admin` cannot bind attributes.
