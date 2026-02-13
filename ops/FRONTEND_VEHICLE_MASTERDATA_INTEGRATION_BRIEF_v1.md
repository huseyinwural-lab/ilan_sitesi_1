# Frontend Vehicle Master Data Integration Brief v1

**Target:** Web / Mobile Client

## 1. Form Logic (Cascading Dropdown)
1.  **Select Brand:**
    -   Fetch `GET /api/vehicles/makes?type=car`.
    -   Render sorted list.
2.  **On Select:**
    -   Clear Model.
    -   Enable Model Dropdown.
    -   Fetch `GET /api/vehicles/models?make_id={id}`.
3.  **Validation:**
    -   Form cannot submit without valid UUIDs for both.

## 2. Localization
-   Backend returns `name` (Global).
-   If `label_{lang}` exists in response, Frontend uses it. (Currently v1 schema only has `name`, so Global name used).

## 3. Passive Records
-   Frontend MUST filter out `is_active=false` items from Dropdowns.
-   BUT Frontend MUST render them if viewing an *existing* old listing (Graceful degradation).
