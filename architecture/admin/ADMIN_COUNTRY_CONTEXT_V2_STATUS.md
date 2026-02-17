# ADMIN_COUNTRY_CONTEXT_V2_STATUS

## Implemented (MVP)
- URL param `?country=XX` backend validate + RBAC scope (400/403)
- /api/users ve /api/dashboard/stats country-aware filtre
- Header UI: Global/Country toggle + country dropdown (URL sync)
- last_selected_country localStorage

## Pending
- Route-guard: country mode aktifken param silinirse otomatik redirect
- Audit log: write işlemlerinde mode/country_scope log
- Apply enforcement to additional admin endpoints as they are implemented
