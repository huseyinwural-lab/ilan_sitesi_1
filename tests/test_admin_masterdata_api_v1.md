# Test Admin MasterData API v1

**Scope:** Integration Tests

## 1. List Attributes
-   Login as Admin.
-   `GET /attributes`.
-   Verify list contains "m2_gross".

## 2. Update Attribute (RBAC)
-   Login as `country_admin`.
-   Try update `is_filterable`.
-   **Expect:** 403 Forbidden.
-   Login as `super_admin`.
-   Update `is_filterable`.
-   **Expect:** 200 OK + Audit Log.

## 3. Binding
-   Login as `super_admin`.
-   Bind "m2_gross" to "Vehicles" (Invalid logic but valid op).
-   **Expect:** 200 OK.
-   Unbind.
-   **Expect:** 200 OK.
