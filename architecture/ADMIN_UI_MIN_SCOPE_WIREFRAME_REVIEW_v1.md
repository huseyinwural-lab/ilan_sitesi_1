# Admin UI Minimum Scope - Wireframe Review Document

**Document ID:** ADMIN_UI_MIN_SCOPE_WIREFRAME_REVIEW_v1  
**Date:** 2026-02-13  
**Status:** 🔒 PENDING FREEZE  
**Sprint:** P7.2  

---

## Purpose

This document serves as the wireframe freeze checkpoint before P7.2 implementation begins. All screens, columns, and behaviors must be reviewed and approved before coding starts.

---

## Screen 1: Attributes Management

### Table Columns

| Column | Field | Sortable | Filterable | Notes |
|--------|-------|----------|------------|-------|
| Key (Slug) | `key` | ✅ | ✅ | Primary identifier, read-only |
| Name (TR) | `name.tr` | ❌ | ❌ | Editable inline |
| Name (DE) | `name.de` | ❌ | ❌ | Editable inline |
| Type | `attribute_type` | ✅ | ✅ | text/number/select/boolean |
| Active | `is_active` | ✅ | ✅ | Toggle (Super Admin only) |
| Filterable | `is_filterable` | ✅ | ✅ | Toggle (Super Admin only) |
| Sort Order | `display_order` | ✅ | ❌ | Editable (Super Admin only) |
| Actions | - | ❌ | ❌ | Edit button |

### Wireframe Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Attributes                                    [+ New Attribute] │
├─────────────────────────────────────────────────────────────────┤
│ 🔍 Search: [_______________]  Status: [All ▼]  Type: [All ▼]   │
├─────────────────────────────────────────────────────────────────┤
│ Key        │ Name (TR)    │ Type   │ Active │ Filter │ Order   │
├────────────┼──────────────┼────────┼────────┼────────┼─────────┤
│ brand      │ Marka        │ select │ ✅     │ ✅     │ 10      │
│ year       │ Yıl          │ number │ ✅     │ ✅     │ 20      │
│ color      │ Renk         │ select │ ✅     │ ❌     │ 30      │
└─────────────────────────────────────────────────────────────────┘
                              [< 1 2 3 ... 5 >]
```

### Review Checklist

- [x] Column `key` shown as read-only (no edit icon)
- [x] `is_active` toggle disabled for Country Admin
- [x] `is_filterable` toggle disabled for Country Admin
- [x] `display_order` field disabled for Country Admin
- [x] Multilingual name fields visible (TR, DE, FR tabs or columns)
- [ ] **PENDING:** Confirm if "New Attribute" button visible to Country Admin

---

## Screen 2: Attribute Options Management

### Context Requirement

Options screen **MUST** be accessed from parent Attribute context:
- URL Pattern: `/admin/attributes/{attribute_id}/options`
- Breadcrumb: `Attributes > {Attribute Name} > Options`

### Table Columns

| Column | Field | Sortable | Filterable | Notes |
|--------|-------|----------|------------|-------|
| Value | `value` | ✅ | ✅ | Internal key, read-only |
| Label (TR) | `label.tr` | ❌ | ❌ | Editable |
| Label (DE) | `label.de` | ❌ | ❌ | Editable |
| Active | `is_active` | ✅ | ✅ | Toggle (Super Admin only) |
| Sort Order | `sort_order` | ✅ | ❌ | Drag-drop or manual |
| Actions | - | ❌ | ❌ | Edit button |

### Wireframe Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Back to Attributes                                            │
│ Options for: "Marka" (brand)                   [+ New Option]   │
├─────────────────────────────────────────────────────────────────┤
│ Value      │ Label (TR)   │ Label (DE)  │ Active │ Order        │
├────────────┼──────────────┼─────────────┼────────┼──────────────┤
│ bmw        │ BMW          │ BMW         │ ✅     │ ≡ 1          │
│ mercedes   │ Mercedes     │ Mercedes    │ ✅     │ ≡ 2          │
│ vw         │ Volkswagen   │ Volkswagen  │ ✅     │ ≡ 3          │
└─────────────────────────────────────────────────────────────────┘
```

### Review Checklist

- [x] Parent Attribute context clearly displayed
- [x] Breadcrumb navigation functional
- [x] `value` field shown as read-only
- [x] `is_active` toggle restricted by role
- [ ] **PENDING:** Drag-drop vs manual sort order input decision

---

## Screen 3: Vehicle Makes/Models Management

### Soft-Delete Policy Reflection

| Action | Behavior | UI Indication |
|--------|----------|---------------|
| Deactivate Make | Sets `is_active=false` | Grayed row + "Inactive" badge |
| Deactivate Model | Sets `is_active=false` | Grayed row + "Inactive" badge |
| View Inactive | Filter toggle | "Show Inactive" checkbox |
| Reactivate | Set `is_active=true` | "Activate" button appears |

**Hard Delete:** NOT SUPPORTED (data integrity requirement)

### Makes Table

| Column | Field | Notes |
|--------|-------|-------|
| Slug | `slug` | Read-only |
| Name (TR) | `label_tr` | Editable |
| Name (DE) | `label_de` | Editable |
| Models Count | computed | Link to models |
| Active | `is_active` | Toggle |
| Actions | - | Edit, View Models |

### Models Table (Nested under Make)

| Column | Field | Notes |
|--------|-------|-------|
| Slug | `slug` | Read-only |
| Name (TR) | `label_tr` | Editable |
| Name (DE) | `label_de` | Editable |
| Active | `is_active` | Toggle |
| Actions | - | Edit |

### Wireframe Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Vehicle Makes                                    [+ New Make]   │
├─────────────────────────────────────────────────────────────────┤
│ ☑ Show Inactive                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Slug       │ Name (TR)    │ Name (DE)   │ Models │ Active       │
├────────────┼──────────────┼─────────────┼────────┼──────────────┤
│ bmw        │ BMW          │ BMW         │ 5 →    │ ✅           │
│ mercedes   │ Mercedes     │ Mercedes    │ 6 →    │ ✅           │
│ togg       │ TOGG         │ TOGG        │ 2 →    │ ✅           │
│ ░░ saab    │ ░░ Saab      │ ░░ Saab     │ 0 →    │ ⬜ Inactive  │
└─────────────────────────────────────────────────────────────────┘
```

### Review Checklist

- [x] Soft-delete shown as "Inactive" status, not removed from list
- [x] Inactive items visually distinct (gray/faded)
- [x] Filter to hide/show inactive items
- [x] No "Delete" button (only Deactivate)
- [x] Models accessible via Make row expansion or link
- [ ] **PENDING:** Confirm "New Make" button role restriction

---

## Screen 4: Role-Based UI Behavior

### Country Admin Field Restrictions

| Screen | Field | Country Admin | Super Admin |
|--------|-------|---------------|-------------|
| Attributes | `key` | Read-only | Read-only |
| Attributes | `name.*` | ✅ Edit | ✅ Edit |
| Attributes | `is_active` | ❌ Disabled | ✅ Edit |
| Attributes | `is_filterable` | ❌ Disabled | ✅ Edit |
| Attributes | `display_order` | ❌ Disabled | ✅ Edit |
| Options | `value` | Read-only | Read-only |
| Options | `label.*` | ✅ Edit | ✅ Edit |
| Options | `is_active` | ❌ Disabled | ✅ Edit |
| Options | `sort_order` | ❌ Disabled | ✅ Edit |
| Makes | `slug` | Read-only | Read-only |
| Makes | `label_*` | ✅ Edit | ✅ Edit |
| Makes | `is_active` | ❌ Disabled | ✅ Edit |
| Models | `slug` | Read-only | Read-only |
| Models | `label_*` | ✅ Edit | ✅ Edit |
| Models | `is_active` | ❌ Disabled | ✅ Edit |

### Visual Indicators for Disabled Controls

```
Super Admin View:          Country Admin View:
┌──────────────┐           ┌──────────────┐
│ Active [✅]  │           │ Active [✅]  │ ← Greyed, no click
│ Filter [✅]  │           │ Filter [✅]  │ ← Greyed, no click
│ Order [___]  │           │ Order [10]   │ ← Read-only text
└──────────────┘           └──────────────┘
```

---

## Gate Status

### Pre-Implementation Gates

| Gate | Status | Blocker |
|------|--------|---------|
| Column definitions confirmed | ✅ | - |
| Options context flow confirmed | ✅ | - |
| Soft-delete policy confirmed | ✅ | - |
| RBAC field restrictions confirmed | ✅ | - |
| New item button visibility | ⏳ | Needs decision |
| Sort order UI method | ⏳ | Needs decision |

### Open Questions

1. **Q1:** Should "New Attribute" button be visible to Country Admin?
   - Option A: Hidden (they can't create, only edit labels)
   - Option B: Visible but disabled with tooltip
   - **Recommendation:** Option A (cleaner UX)

2. **Q2:** Sort order editing method?
   - Option A: Manual number input
   - Option B: Drag-drop reordering
   - **Recommendation:** Option A for MVP (simpler implementation)

---

## Freeze Approval

| Reviewer | Status | Date |
|----------|--------|------|
| Technical Review | ✅ Approved | 2026-02-13 |
| Product Review | ⏳ Pending | - |

**GATE:** This document must be marked as "FROZEN" before P7.2 implementation begins.

---

## References

- `/app/architecture/ADMIN_API_MASTERDATA_MIN_V1_FINAL.md`
- `/app/architecture/ADMIN_RBAC_MASTERDATA_MATRIX_v1.md`
- `/app/backend/app/routers/admin_mdm_routes.py`
