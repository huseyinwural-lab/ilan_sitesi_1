# ADMIN_COUNTRY_CONTEXT_V2_IMPLEMENTATION_NOTES

## Backend
- `resolve_admin_country_context(request, current_user, db)` dependency:
  - ?country yoksa global
  - ?country varsa validate + RBAC scope
  - request.state.admin_country_ctx set edilir

## Frontend
- Mode toggle URL’i yönetir:
  - Global => country param sil
  - Country => country param set (last_selected fallback)

## Limitasyonlar (MVP)
- Country mode şu an URL’de country varsa aktif kabul edilir.
- Param silinmesi zorunlu redirect: sonraki iterasyonda route-guard ile %100 enforce edilecek.
