# Admin UI RBAC Behavior Matrix

**Document ID:** ADMIN_UI_RBAC_BEHAVIOR_MATRIX_v1  
**Date:** 2026-02-13  
**Status:** 📋 REFERENCE  
**Sprint:** P7.2  

---

## Purpose

This document defines the exact UI behavior for each role when interacting with Admin Master Data screens. It ensures no incorrect permission displays occur.

---

## 1. Role Definitions

| Role | Code | Scope | Description |
|------|------|-------|-------------|
| Super Admin | `super_admin` | Global | Full access to all fields and actions |
| Country Admin | `country_admin` | Country-scoped | Label editing only |
| Moderator | `moderator` | - | No access to Master Data |
| Support | `support` | - | No access to Master Data |
| Finance | `finance` | - | No access to Master Data |

---

## 2. Menu Visibility

| Menu Item | super_admin | country_admin | moderator | support | finance |
|-----------|-------------|---------------|-----------|---------|---------|
| Master Data | ✅ Visible | ✅ Visible | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| ├─ Attributes | ✅ | ✅ | ❌ | ❌ | ❌ |
| ├─ Vehicle Makes | ✅ | ✅ | ❌ | ❌ | ❌ |
| └─ Vehicle Models | ✅ | ✅ | ❌ | ❌ | ❌ |

---

## 3. Attributes Screen

### Field-Level Permissions

| Field | super_admin | country_admin | UI Behavior |
|-------|-------------|---------------|-------------|
| `key` | Read-only | Read-only | Text display, no input |
| `attribute_type` | Read-only | Read-only | Badge/chip display |
| `name.tr` | ✅ Edit | ✅ Edit | Inline text input |
| `name.de` | ✅ Edit | ✅ Edit | Inline text input |
| `name.en` | ✅ Edit | ✅ Edit | Inline text input |
| `name.fr` | ✅ Edit | ✅ Edit | Inline text input |
| `is_active` | ✅ Toggle | ❌ Disabled | See behavior below |
| `is_filterable` | ✅ Toggle | ❌ Disabled | See behavior below |
| `display_order` | ✅ Input | ❌ Disabled | See behavior below |

### Disabled Field Behaviors

#### Toggle Switches (is_active, is_filterable)

**Super Admin:**
```
┌─────────────────┐
│ Aktif  [●━━━━━] │  ← Clickable, green when on
└─────────────────┘
```

**Country Admin:**
```
┌─────────────────┐
│ Aktif  [●━━━━━] │  ← Greyed out, cursor: not-allowed
│         ↑       │     Tooltip: "Sadece Super Admin değiştirebilir"
└─────────────────┘
```

#### Number Input (display_order)

**Super Admin:**
```
┌─────────────────┐
│ Sıra: [  10  ]  │  ← Editable input
└─────────────────┘
```

**Country Admin:**
```
┌─────────────────┐
│ Sıra:    10     │  ← Plain text, no input
└─────────────────┘
```

### Action Button Visibility

| Button | super_admin | country_admin |
|--------|-------------|---------------|
| Edit (inline) | ✅ Visible | ✅ Visible (label fields only) |
| New Attribute | ✅ Visible | ❌ Hidden |
| Delete | ❌ N/A (soft delete) | ❌ N/A |
| Deactivate | ✅ Visible | ❌ Hidden |

---

## 4. Options Screen

### Field-Level Permissions

| Field | super_admin | country_admin | UI Behavior |
|-------|-------------|---------------|-------------|
| `value` | Read-only | Read-only | Text display |
| `label.tr` | ✅ Edit | ✅ Edit | Inline text input |
| `label.de` | ✅ Edit | ✅ Edit | Inline text input |
| `label.en` | ✅ Edit | ✅ Edit | Inline text input |
| `is_active` | ✅ Toggle | ❌ Disabled | Greyed toggle |
| `sort_order` | ✅ Input/Drag | ❌ Disabled | Read-only display |

### Action Button Visibility

| Button | super_admin | country_admin |
|--------|-------------|---------------|
| New Option | ✅ Visible | ❌ Hidden |
| Reorder | ✅ Visible | ❌ Hidden |
| Deactivate | ✅ Visible | ❌ Hidden |

---

## 5. Vehicle Makes Screen

### Field-Level Permissions

| Field | super_admin | country_admin | UI Behavior |
|-------|-------------|---------------|-------------|
| `slug` | Read-only | Read-only | Text display |
| `label_tr` | ✅ Edit | ✅ Edit | Inline text input |
| `label_de` | ✅ Edit | ✅ Edit | Inline text input |
| `label_fr` | ✅ Edit | ✅ Edit | Inline text input |
| `is_active` | ✅ Toggle | ❌ Disabled | Greyed toggle |
| Models Count | Read-only | Read-only | Link to models |

### Action Button Visibility

| Button | super_admin | country_admin |
|--------|-------------|---------------|
| New Make | ✅ Visible | ❌ Hidden |
| View Models | ✅ Visible | ✅ Visible |
| Deactivate | ✅ Visible | ❌ Hidden |
| Activate | ✅ Visible | ❌ Hidden |

---

## 6. Vehicle Models Screen

### Field-Level Permissions

| Field | super_admin | country_admin | UI Behavior |
|-------|-------------|---------------|-------------|
| `slug` | Read-only | Read-only | Text display |
| `label_tr` | ✅ Edit | ✅ Edit | Inline text input |
| `label_de` | ✅ Edit | ✅ Edit | Inline text input |
| `label_fr` | ✅ Edit | ✅ Edit | Inline text input |
| `is_active` | ✅ Toggle | ❌ Disabled | Greyed toggle |

### Action Button Visibility

| Button | super_admin | country_admin |
|--------|-------------|---------------|
| New Model | ✅ Visible | ❌ Hidden |
| Deactivate | ✅ Visible | ❌ Hidden |
| Activate | ✅ Visible | ❌ Hidden |

---

## 7. Error Handling by Role

### 403 Forbidden Response Scenarios

| Scenario | Trigger | UI Response |
|----------|---------|-------------|
| Country Admin toggles is_active | Click on disabled toggle | No action (disabled) |
| Country Admin sends PATCH with is_active | API call (shouldn't happen) | Toast + revert |
| Non-admin accesses /admin/master-data | Navigation attempt | Redirect to /dashboard |

### Frontend Guard Pattern

```typescript
// Permission check helper
function canEditField(field: string, role: string): boolean {
  const configFields = ['is_active', 'is_filterable', 'display_order', 'sort_order'];
  
  if (configFields.includes(field)) {
    return role === 'super_admin';
  }
  
  return ['super_admin', 'country_admin'].includes(role);
}

// Usage in component
<Toggle 
  disabled={!canEditField('is_active', user.role)}
  title={!canEditField('is_active', user.role) ? 
    'Sadece Super Admin değiştirebilir' : undefined}
/>
```

---

## 8. Visual Design Specifications

### Disabled Control Styling

```css
/* Disabled toggle */
.toggle-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

/* Disabled input */
.input-disabled {
  background-color: #f5f5f5;
  color: #888;
  border: none;
  cursor: not-allowed;
}

/* Hidden button (for country admin) */
.btn-role-hidden {
  display: none;
}
```

### Tooltip Text (Turkish)

| Field | Tooltip |
|-------|---------|
| is_active (disabled) | "Bu alanı sadece Super Admin değiştirebilir" |
| is_filterable (disabled) | "Bu alanı sadece Super Admin değiştirebilir" |
| display_order (disabled) | "Sıralama sadece Super Admin tarafından düzenlenebilir" |
| New button (hidden) | N/A - button not shown |

---

## 9. Summary Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    RBAC BEHAVIOR MATRIX                         │
├─────────────────────────────────────────────────────────────────┤
│                        │ Super Admin │ Country Admin            │
├────────────────────────┼─────────────┼──────────────────────────┤
│ View Master Data       │     ✅      │      ✅                  │
│ Edit Labels            │     ✅      │      ✅                  │
│ Edit is_active         │     ✅      │      ❌ (disabled)       │
│ Edit is_filterable     │     ✅      │      ❌ (disabled)       │
│ Edit sort_order        │     ✅      │      ❌ (disabled)       │
│ Create New Items       │     ✅      │      ❌ (hidden)         │
│ Deactivate Items       │     ✅      │      ❌ (hidden)         │
│ View Inactive Items    │     ✅      │      ✅                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- `/app/backend/app/routers/admin_mdm_routes.py` (lines 56-82)
- `/app/architecture/ADMIN_RBAC_MASTERDATA_MATRIX_v1.md`
- `/app/architecture/ADMIN_UI_API_MAPPING_v1.md`
