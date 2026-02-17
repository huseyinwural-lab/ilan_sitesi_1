# ADMIN_COUNTRY_CONTEXT_V2_DISABLED_COUNTRY_POLICY

MVP policy:
- Disabled country still passes validation for admin access.

Optional stricter policy:
- If country.is_enabled == false and user not super_admin => 403
