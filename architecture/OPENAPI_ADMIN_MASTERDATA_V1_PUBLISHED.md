# OpenAPI Admin MasterData v1

**Format:** OpenAPI 3.0 (YAML/JSON)
**Source:** FastAPI Auto-Generated (`/docs`)

## 1. Endpoints Overview
| Method | Path | Summary | Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/attributes` | List Attributes | Any Admin |
| `PATCH` | `/attributes/{id}` | Update Attribute | Super (Config), Country (Label) |
| `GET` | `/attributes/{id}/options` | List Options | Any Admin |
| `PATCH` | `/options/{id}` | Update Option | Super (Config), Country (Label) |
| `GET` | `/categories/{id}/attributes`| List Bindings | Any Admin |
| `POST` | `/categories/{id}/bind` | Bind Attribute | Super Admin |
| `DELETE`| `/categories/{id}/bind/{id}`| Unbind Attribute | Super Admin |

## 2. Schema Examples
### Attribute Object
```json
{
  "id": "uuid",
  "key": "m2_gross",
  "name": {"en": "Gross Area", "tr": "Brüt Alan"},
  "attribute_type": "number",
  "is_filterable": true,
  "is_active": true
}
```

### 403 Forbidden Response
```json
{
  "detail": "Only Super Admin can change configuration"
}
```
