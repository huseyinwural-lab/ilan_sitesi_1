# Admin RBAC MasterData Matrix v1

**Roles:** `super_admin` vs `country_admin` (and others)

| Resource | Action | Role: Super Admin | Role: Country Admin | Note |
| :--- | :--- | :--- | :--- | :--- |
| **Attribute** | Read | ✅ | ✅ | |
| **Attribute** | Update (Label) | ✅ | ✅ | Localizers can fix typos |
| **Attribute** | Update (Config) | ✅ | ❌ | Only Super Admin toggles filters |
| **Option** | Create | ✅ | ❌ | Structural change |
| **Option** | Update | ✅ | ✅ | Label only |
| **Binding** | Create/Delete | ✅ | ❌ | Structural change |

**Implementation:** Use `check_permissions(["super_admin"])` decorator for critical routes.
