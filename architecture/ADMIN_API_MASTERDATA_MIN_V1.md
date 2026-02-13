# Admin API MasterData Min v1

**Prefix:** `/api/admin/master-data`

## 1. Endpoints
-   `GET /attributes`: List all.
-   `PATCH /attributes/{id}`: Update label/status.
-   `POST /attributes/{id}/options`: Add option.
-   `PATCH /options/{id}`: Update option label/status.
-   `POST /categories/{id}/bind`: Bind attribute.
-   `DELETE /categories/{id}/bind/{attr_id}`: Unbind.

## 2. Access
-   **Super Admin:** All.
-   **Country Admin:** View Only (or Label Edit only).
