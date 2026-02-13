# P7 Admin UI Min Scope Plan v1

**Goal:** Master Data Management.

## 1. Screens
1.  **Attribute Management:**
    -   List all Attributes.
    -   Toggle `is_active`.
    -   Edit Labels (TR/DE/FR).
2.  **Option Management:**
    -   Drill-down into Attribute.
    -   Add/Edit/Disable Options.
3.  **Category Binding:**
    -   Tree View of Categories.
    -   Show bound Attributes.
    -   (Super Admin) Add/Remove Binding.

## 2. Audit
-   Every change logs `ADMIN_UPDATE_MASTERDATA`.

## 3. Restrictions
-   **No Delete:** Hard delete disabled. Only `is_active=False`.
-   **No Type Change:** Cannot change `Select` to `Number` after creation.
