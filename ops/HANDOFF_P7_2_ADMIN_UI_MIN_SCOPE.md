# Handoff: P7.2 Admin UI Minimum Scope

**Target:** Frontend Team
**Stack:** React / Vue / Angular (Admin Panel)

## 1. Attributes Page (`/admin/attributes`)
-   **Table Columns:** Key, Type, TR/EN Labels, Filterable (Toggle), Active (Toggle), Actions.
-   **Logic:**
    -   "Filterable" toggle disabled for `country_admin`.
    -   "Edit" opens Modal.

## 2. Edit Attribute Modal
-   **Tabs:** Config (Super Admin), Labels (All).
-   **Labels:** Inputs for `en`, `tr`, `de`, `fr`.
-   **Config:** Checkboxes for `is_filterable`, `is_active`.

## 3. Options Page (`/admin/attributes/{id}/options`)
-   **List:** Sortable list of options.
-   **Actions:** Edit Label, Toggle Active.
-   **Drag & Drop:** Update `sort_order` (Patch endpoint).

## 4. Category Binding (`/admin/categories`)
-   **View:** Tree view of categories.
-   **Detail:** Selecting a leaf category shows "Bound Attributes".
-   **Add Binding:** Dropdown of available attributes (Super Admin).
