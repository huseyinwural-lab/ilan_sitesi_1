# ADMIN_COUNTRY_CONTEXT_V2_SECURITY

## Tehdit
- Admin’in yanlış ülkeye operasyon yapması

## Önlem
- URL param primary (deterministic)
- Backend validation (400)
- RBAC scope enforcement (403)
- Audit log’a mode+country_scope ekleme
