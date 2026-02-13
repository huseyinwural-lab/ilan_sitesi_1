# Admin User Creation Spec

**Feature:** Allow Super Admin to manually create system users.
**Endpoint:** `POST /api/admin/users`

## 1. Access Control
-   **Allowed Role:** `super_admin` ONLY.
-   **Target Roles:** Can create `super_admin`, `country_admin`, `moderator`, `support`, `finance`.

## 2. Request Body
```json
{
  "email": "new.admin@platform.com",
  "password": "TemporaryPassword123!",
  "full_name": "New Admin",
  "role": "moderator",
  "country_scope": ["TR", "DE"] // Optional
}
```

## 3. Business Logic
1.  Check if email exists -> 400 Bad Request.
2.  Hash password.
3.  Set `is_active = True`.
4.  Set `is_verified = True` (Since admin created it).
5.  Audit Log: Action `ADMIN_CREATE_USER`.

## 4. Response
`201 Created` -> User Object (without password).
