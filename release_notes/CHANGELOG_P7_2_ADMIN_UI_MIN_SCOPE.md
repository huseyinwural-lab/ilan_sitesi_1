# CHANGELOG: P7.2 Admin UI Minimum Scope

**Version:** P7.2  
**Release Date:** 2026-02-13  
**Status:** ✅ COMPLETE  

---

## Summary

P7.2 delivered a functional Admin UI for Master Data Management, enabling Super Admins and Country Admins to manage Attributes, Attribute Options, and Vehicle Makes/Models with proper RBAC enforcement.

---

## New Features

### 1. Admin Attributes Management (`/admin/master-data/attributes`)

- **List View:** Display all attributes with search and filter capabilities
- **Inline Editing:** Edit attribute labels (TR, DE) directly in the table
- **Super Admin Controls:** Toggle `is_active`, `is_filterable`, edit `display_order`
- **Country Admin Restrictions:** Only label editing allowed
- **Options Navigation:** Direct link to manage options for select-type attributes

### 2. Admin Options Management (`/admin/master-data/attributes/{id}/options`)

- **Parent Context:** Breadcrumb navigation showing parent attribute
- **List View:** Display all options for selected attribute
- **Inline Editing:** Edit option labels (TR, DE, EN)
- **Super Admin Controls:** Toggle `is_active`, edit `sort_order`
- **Country Admin Restrictions:** Only label editing allowed

### 3. Admin Vehicle MDM (`/admin/master-data/vehicle-makes`)

- **Makes View:** List all vehicle makes with inline label editing
- **Models View:** Drill-down from make to view/edit models
- **Soft-Delete Policy:** No hard delete, only `is_active` toggle
- **Inactive Filter:** Checkbox to show/hide inactive items
- **Visual Distinction:** Inactive items shown with reduced opacity

---

## API Additions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/master-data/vehicle-makes` | GET | List all vehicle makes |
| `/api/v1/admin/master-data/vehicle-makes/{id}` | GET, PATCH | Get/Update single make |
| `/api/v1/admin/master-data/vehicle-makes/{id}/models` | GET | List models for make |
| `/api/v1/admin/master-data/vehicle-models/{id}` | PATCH | Update vehicle model |

---

## RBAC Behavior

| Role | Attributes | Options | Vehicle MDM |
|------|------------|---------|-------------|
| Super Admin | Full access | Full access | Full access |
| Country Admin | Labels only | Labels only | Labels only |
| Moderator | No access | No access | No access |
| Support | No access | No access | No access |
| Finance | No access | No access | No access |

---

## Files Added

```
/app/frontend/src/pages/
├── AdminAttributes.js    # Attributes management
├── AdminOptions.js       # Options management (with breadcrumb)
└── AdminVehicleMDM.js    # Vehicle Makes/Models management

/app/release_notes/
├── P7_2_KICKOFF_ADMIN_UI_MIN_SCOPE.md

/app/ops/
├── P7_2_SCREEN1_ATTRIBUTES_UI_ACCEPTANCE.md
├── P7_2_SCREEN2_OPTIONS_UI_ACCEPTANCE.md
├── P7_2_SCREEN3_VEHICLE_MDM_UI_ACCEPTANCE.md
├── P7_2_UI_TO_API_SMOKE_REPORT.md
└── STAGING_VALIDATE_ADMIN_TO_SEARCH_P7_2.md
```

---

## Known Limitations

1. **No Create:** Cannot create new attributes/options/makes/models (out of MVP scope)
2. **No Bulk Operations:** Single item editing only
3. **No Drag-Drop:** Sort order via manual number input
4. **No French Labels Column:** Space constraint - could add if needed
5. **No Pagination:** API returns all items (works for current data size)

---

## Operational Notes

### Admin Access

- **URL:** `/admin/master-data/attributes` or `/admin/master-data/vehicle-makes`
- **Access:** Super Admin and Country Admin only
- **Menu:** Under "Master Data" section in sidebar

### Audit Logging

All admin changes are automatically logged:
- Attribute updates
- Option updates
- Vehicle make/model updates

View logs in `/audit-logs` page.

### Soft-Delete Policy

- **No hard delete** for any master data
- Use `is_active` toggle to deactivate
- Inactive items remain in database for data integrity
- Filter to show/hide inactive items in UI

---

## Testing

- **API Tests:** All endpoints verified via curl
- **UI Tests:** Visual testing completed
- **RBAC Tests:** Backend enforcement verified
- **Integration Tests:** Admin→Search scenarios validated

---

## Next Steps (P7.3)

1. **Public UI Search Integration:** Use new MDM data in public search
2. **Category-Attribute Binding UI:** Manage which attributes appear on which categories
3. **Expanded Facets:** Full facet integration with Search API v2

---

## References

- Wireframes: `/app/architecture/ADMIN_UI_MIN_SCOPE_WIREFRAME_REVIEW_v1.md`
- API Mapping: `/app/architecture/ADMIN_UI_API_MAPPING_v1.md`
- RBAC Matrix: `/app/architecture/ADMIN_UI_RBAC_BEHAVIOR_MATRIX_v1.md`
- Sprint Backlog: `/app/tasks/P7_2_ADMIN_UI_SPRINT_BACKLOG_v1.md`
