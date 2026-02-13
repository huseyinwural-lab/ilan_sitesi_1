# Staging Smoke: Admin MasterData v1

**Goal:** Verify Admin -> Search Feedback Loop.

## 1. Label Update
1.  **Actor:** Country Admin (TR).
2.  **Action:** `PATCH /attributes/{id}` -> Set `name.tr` = "Oda Sayısı (Yeni)".
3.  **Check:** Call `GET /api/v2/search`. Facet label should be "Oda Sayısı (Yeni)".

## 2. Filter Toggle
1.  **Actor:** Super Admin.
2.  **Action:** `PATCH /attributes/{id}` -> Set `is_filterable` = `false`.
3.  **Check:** Call `GET /api/v2/search`. Attribute should **disappear** from Facets.

## 3. Option Deactivation
1.  **Actor:** Super Admin.
2.  **Action:** `PATCH /options/{id}` -> Set `is_active` = `false`.
3.  **Check:** Call `GET /api/v2/search`. Option should **disappear** from Facet list.
