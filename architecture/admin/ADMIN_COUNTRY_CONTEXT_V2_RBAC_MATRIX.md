# ADMIN_COUNTRY_CONTEXT_V2_RBAC_MATRIX

| Role | country_scope | Access |
|------|--------------|--------|
| super_admin | ['*'] | Any country |
| country_admin | ['DE'] | Only DE |
| finance | ['DE'] | Only DE (if endpoint enforces) |
| moderator | ['DE'] | Only DE (if endpoint enforces) |

Note: In this repo, country_scope drives enforcement.
