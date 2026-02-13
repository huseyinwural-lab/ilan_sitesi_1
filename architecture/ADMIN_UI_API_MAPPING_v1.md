# Admin UI API-UI Mapping Document

**Document ID:** ADMIN_UI_API_MAPPING_v1  
**Date:** 2026-02-13  
**Status:** 📋 REFERENCE  
**Sprint:** P7.2  

---

## Purpose

This document maps each Admin UI screen to its corresponding API endpoints, defines PATCH field whitelists, and specifies error handling behaviors.

---

## 1. Attributes Screen

### Endpoints

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List | GET | `/api/v1/admin/master-data/attributes` | Supports `q`, `is_active` params |
| Update | PATCH | `/api/v1/admin/master-data/attributes/{id}` | Partial update |

### GET Parameters

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `q` | string | No | Search by key (ilike) |
| `is_active` | boolean | No | Filter by active status |

### PATCH Field Whitelist

| Field | Type | Country Admin | Super Admin |
|-------|------|---------------|-------------|
| `name` | `Dict[str, str]` | ✅ | ✅ |
| `is_active` | `boolean` | ❌ 403 | ✅ |
| `is_filterable` | `boolean` | ❌ 403 | ✅ |
| `display_order` | `integer` | ❌ 403 | ✅ |

### Response Schema

```json
{
  "id": "uuid",
  "key": "string",
  "name": {"tr": "...", "de": "...", "en": "..."},
  "attribute_type": "text|number|select|boolean",
  "is_active": true,
  "is_filterable": true,
  "display_order": 10
}
```

---

## 2. Options Screen

### Endpoints

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List | GET | `/api/v1/admin/master-data/attributes/{id}/options` | Requires attribute context |
| Update | PATCH | `/api/v1/admin/master-data/options/{id}` | Partial update |

### PATCH Field Whitelist

| Field | Type | Country Admin | Super Admin |
|-------|------|---------------|-------------|
| `label` | `Dict[str, str]` | ✅ | ✅ |
| `is_active` | `boolean` | ❌ 403 | ✅ |
| `sort_order` | `integer` | ❌ 403 | ✅ |

### Response Schema

```json
{
  "id": "uuid",
  "attribute_id": "uuid",
  "value": "string",
  "label": {"tr": "...", "de": "..."},
  "is_active": true,
  "sort_order": 1
}
```

---

## 3. Vehicle Makes Screen

### Endpoints

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List | GET | `/api/v1/admin/master-data/vehicle-makes` | All makes |
| Get One | GET | `/api/v1/admin/master-data/vehicle-makes/{id}` | Single make |
| Update | PATCH | `/api/v1/admin/master-data/vehicle-makes/{id}` | Partial update |
| Create | POST | `/api/v1/admin/master-data/vehicle-makes` | Super Admin only |

### PATCH Field Whitelist

| Field | Type | Country Admin | Super Admin |
|-------|------|---------------|-------------|
| `label_tr` | `string` | ✅ | ✅ |
| `label_de` | `string` | ✅ | ✅ |
| `label_fr` | `string` | ✅ | ✅ |
| `is_active` | `boolean` | ❌ 403 | ✅ |

---

## 4. Vehicle Models Screen

### Endpoints

| Action | Method | Endpoint | Notes |
|--------|--------|----------|-------|
| List | GET | `/api/v1/admin/master-data/vehicle-makes/{make_id}/models` | Models for make |
| Update | PATCH | `/api/v1/admin/master-data/vehicle-models/{id}` | Partial update |
| Create | POST | `/api/v1/admin/master-data/vehicle-makes/{make_id}/models` | Super Admin only |

### PATCH Field Whitelist

| Field | Type | Country Admin | Super Admin |
|-------|------|---------------|-------------|
| `label_tr` | `string` | ✅ | ✅ |
| `label_de` | `string` | ✅ | ✅ |
| `label_fr` | `string` | ✅ | ✅ |
| `is_active` | `boolean` | ❌ 403 | ✅ |

---

## 5. Error Handling UI Behaviors

### HTTP Status Code Mapping

| Status | Code | UI Behavior |
|--------|------|-------------|
| **401** | `unauthorized` | Redirect to login |
| **403** | `permission_denied` | Toast: "Bu işlem için yetkiniz yok" + Revert field |
| **404** | `resource_not_found` | Toast: "Kayıt bulunamadı" + Refresh list |
| **422** | `validation_error` | Inline field error message |
| **429** | `rate_limited` | Toast: "Çok fazla istek, lütfen bekleyin" |
| **500** | `internal_error` | Toast: "Sistem hatası, lütfen tekrar deneyin" |

### Error Response Handling

```typescript
// Frontend Error Handler Pattern
async function handleApiError(error: ApiError) {
  const { status, data } = error.response;
  
  switch (status) {
    case 401:
      router.push('/login');
      break;
    case 403:
      toast.error('Bu işlem için yetkiniz yok');
      revertFieldValue(); // Undo optimistic update
      break;
    case 404:
      toast.error('Kayıt bulunamadı');
      refreshList();
      break;
    case 422:
      setFieldError(data.message);
      break;
    case 429:
      toast.warning('Çok fazla istek, lütfen bekleyin');
      break;
    default:
      toast.error(`Hata: ${data.message || 'Bilinmeyen hata'}`);
  }
}
```

### Optimistic Update Pattern

For inline editing:

1. Show loading spinner on field
2. Apply change optimistically
3. Send PATCH request
4. On success: Remove spinner, show success tick
5. On error: Revert value, show error toast

```
User Action → Optimistic UI → API Call → Success/Revert
    │              │             │            │
    └──────────────┴─────────────┴────────────┘
                   ~200ms total perceived delay
```

---

## 6. Field Validation Rules

### Client-Side Validation

| Field | Validation | Error Message |
|-------|------------|---------------|
| `name.tr` | Required, max 100 chars | "Türkçe isim zorunlu" |
| `name.de` | Required, max 100 chars | "Almanca isim zorunlu" |
| `label_tr` | Required, max 100 chars | "Türkçe etiket zorunlu" |
| `display_order` | Integer, 0-9999 | "Geçersiz sıra numarası" |
| `sort_order` | Integer, 0-9999 | "Geçersiz sıra numarası" |

### Server-Side Validation (422 Response)

```json
{
  "code": "validation_error",
  "message": "Validation failed",
  "details": [
    {"field": "name.tr", "message": "Field is required"}
  ]
}
```

---

## 7. API Authentication

### Headers Required

```
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### Token Refresh Flow

1. Access token expires (401 response)
2. Attempt refresh with refresh token
3. On success: Retry original request
4. On failure: Redirect to login

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│ ADMIN UI → API QUICK REFERENCE                                 │
├────────────────────────────────────────────────────────────────┤
│ Attributes List    → GET  /api/v1/admin/master-data/attributes │
│ Attributes Update  → PATCH /api/v1/admin/master-data/attr/{id} │
│ Options List       → GET  /api/v1/admin/.../attributes/{id}/options │
│ Options Update     → PATCH /api/v1/admin/master-data/options/{id} │
│ Makes List         → GET  /api/v1/admin/master-data/vehicle-makes │
│ Makes Update       → PATCH /api/v1/admin/.../vehicle-makes/{id} │
│ Models List        → GET  /api/v1/admin/.../makes/{id}/models  │
│ Models Update      → PATCH /api/v1/admin/.../vehicle-models/{id} │
├────────────────────────────────────────────────────────────────┤
│ RBAC: Country Admin → Only label fields                        │
│ RBAC: Super Admin   → All fields including is_active           │
└────────────────────────────────────────────────────────────────┘
```

---

## References

- `/app/backend/app/routers/admin_mdm_routes.py`
- `/app/architecture/API_ERROR_CONTRACT.md`
- `/app/architecture/ADMIN_RBAC_MASTERDATA_MATRIX_v1.md`
