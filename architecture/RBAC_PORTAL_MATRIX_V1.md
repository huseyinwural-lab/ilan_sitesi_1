# RBAC_PORTAL_MATRIX_V1

| Role | Portal Scope | Portal | Notlar |
|------|--------------|--------|-------|
| super_admin | admin | /admin | Tüm admin modüller |
| country_admin | admin | /admin | Ülke kapsamlı admin |
| moderator | admin | /admin | Moderasyon |
| support | admin | /admin | Destek süreçleri |
| finance | admin | /admin | Finans |
| campaigns_admin | admin | /admin | Kampanya yönetimi |
| campaigns_supervisor | admin | /admin | Kampanya gözetimi |
| ROLE_AUDIT_VIEWER | admin | /admin | Audit view-only |
| dealer | dealer | /dealer | Kurumsal panel |
| individual | account | /account | Bireysel panel |

## JWT Standardı
```
{ user_id, role, portal_scope }
```
