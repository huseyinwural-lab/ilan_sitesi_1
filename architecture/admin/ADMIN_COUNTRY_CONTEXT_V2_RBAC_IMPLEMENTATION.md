# ADMIN_COUNTRY_CONTEXT_V2_RBAC_IMPLEMENTATION

Backend enforcement uses `country_scope` on user document:
- If contains '*': unrestricted
- Else: must include requested country

Recommended:
- Keep `country_code` for default UX only
- Keep `country_scope` as the authoritative restriction list
