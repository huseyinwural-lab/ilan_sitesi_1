# Admin API MasterData Min v1 Final

**Base URL:** `/api/v1/admin/master-data`

## 1. Attributes
-   **GET /attributes**
    -   Query: `type`, `is_active`, `q` (search name)
    -   Response: `[Attribute]`
-   **PATCH /attributes/{id}**
    -   Body: `name` (dict), `is_active`, `is_filterable`, `sort_order`
    -   Forbidden: `key`, `attribute_type`

## 2. Options
-   **GET /attributes/{id}/options**
    -   Response: `[AttributeOption]` sorted by `sort_order`
-   **PATCH /options/{id}**
    -   Body: `label` (dict), `is_active`, `sort_order`
    -   Forbidden: `value`

## 3. Category Bindings
-   **GET /categories/{id}/attributes**
    -   Response: `[{attribute, is_required_override, inherit}]`
-   **POST /categories/{id}/bind**
    -   Body: `attribute_id`, `is_required`, `inherit`
    -   **Super Admin ONLY**

## 4. Audit
-   Every write operation MUST create an `AuditLog` entry.
