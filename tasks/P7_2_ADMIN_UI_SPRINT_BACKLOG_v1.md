# P7.2 Admin UI Sprint Backlog

**Document ID:** P7_2_ADMIN_UI_SPRINT_BACKLOG_v1  
**Date:** 2026-02-13  
**Status:** 🔒 LOCKED  
**Sprint Duration:** TBD  

---

## Sprint Goal

Deliver a functional Admin UI for Master Data management, enabling Super Admins and Country Admins to manage Attributes, Options, and Vehicle Makes/Models with proper RBAC enforcement.

---

## Prerequisites (Gates)

| Gate | Status | Document |
|------|--------|----------|
| P7.0 Closure | ✅ PASS | `/app/release_notes/PHASE_CLOSE_P7_0_STABILIZATION.md` |
| Wireframe Freeze | ✅ FROZEN | `/app/architecture/ADMIN_UI_MIN_SCOPE_WIREFRAME_REVIEW_v1.md` |
| API Mapping | ✅ COMPLETE | `/app/architecture/ADMIN_UI_API_MAPPING_v1.md` |
| RBAC Matrix | ✅ COMPLETE | `/app/architecture/ADMIN_UI_RBAC_BEHAVIOR_MATRIX_v1.md` |

---

## Backlog Items

### Screen 1: Attributes Management

**Priority:** P0 (Must Have)

#### User Stories

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| AT-01 | As Super Admin, I can view all attributes | List displays key, name, type, is_active, is_filterable |
| AT-02 | As Super Admin, I can filter attributes by status | Dropdown filter works |
| AT-03 | As Super Admin, I can search attributes by key | Search input filters list |
| AT-04 | As Super Admin, I can edit attribute name (all languages) | Inline edit saves via PATCH |
| AT-05 | As Super Admin, I can toggle is_active | Toggle updates via PATCH |
| AT-06 | As Super Admin, I can toggle is_filterable | Toggle updates via PATCH |
| AT-07 | As Country Admin, I can only edit name fields | is_active/is_filterable disabled |
| AT-08 | As Admin, I see Options link for select-type attributes | Link navigates to options |

#### Technical Tasks

- [ ] Create `/admin/master-data/attributes` route
- [ ] Implement `AttributeList` component
- [ ] Implement `AttributeRow` with inline editing
- [ ] Implement `AttributeFilters` (search, status)
- [ ] Connect to `GET /api/v1/admin/master-data/attributes`
- [ ] Implement PATCH for inline updates
- [ ] Add RBAC-based field disabling
- [ ] Add loading states and error handling
- [ ] Add data-testid attributes

#### Done Criteria

- [ ] All user stories pass manual testing
- [ ] RBAC restrictions enforced correctly
- [ ] Error toasts shown for failures
- [ ] Audit log created on updates

---

### Screen 2: Attribute Options Management

**Priority:** P0 (Must Have)

#### User Stories

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| OP-01 | As Admin, I navigate to options from attribute row | URL: `/admin/attributes/{id}/options` |
| OP-02 | As Admin, I see breadcrumb with parent attribute | "Attributes > {name} > Options" |
| OP-03 | As Super Admin, I can view all options | List shows value, label, is_active, sort_order |
| OP-04 | As Super Admin, I can edit option labels | Inline edit saves via PATCH |
| OP-05 | As Super Admin, I can toggle option is_active | Toggle updates via PATCH |
| OP-06 | As Super Admin, I can change sort_order | Manual input or drag-drop |
| OP-07 | As Country Admin, I can only edit labels | is_active/sort_order disabled |

#### Technical Tasks

- [ ] Create `/admin/master-data/attributes/:id/options` route
- [ ] Implement `OptionList` component with parent context
- [ ] Implement `OptionRow` with inline editing
- [ ] Implement breadcrumb navigation
- [ ] Connect to `GET /api/v1/admin/master-data/attributes/{id}/options`
- [ ] Implement PATCH for option updates
- [ ] Add RBAC-based field disabling
- [ ] Add back navigation to attributes

#### Done Criteria

- [ ] Parent attribute context always visible
- [ ] Breadcrumb navigation functional
- [ ] RBAC restrictions enforced
- [ ] Changes reflect immediately in list

---

### Screen 3: Vehicle Makes/Models Management

**Priority:** P0 (Must Have)

#### User Stories

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| VM-01 | As Admin, I can view all vehicle makes | List shows slug, labels, model count, is_active |
| VM-02 | As Admin, I can filter to show/hide inactive | Checkbox filter works |
| VM-03 | As Super Admin, I can edit make labels | Inline edit saves via PATCH |
| VM-04 | As Super Admin, I can toggle make is_active | Toggle updates, row becomes greyed |
| VM-05 | As Admin, I can navigate to models for a make | Link/button shows models |
| VM-06 | As Super Admin, I can edit model labels | Inline edit saves via PATCH |
| VM-07 | As Super Admin, I can toggle model is_active | Toggle updates |
| VM-08 | As Country Admin, I can only edit labels | is_active toggle disabled |
| VM-09 | As Admin, inactive items are visually distinct | Grey/faded styling |

#### Technical Tasks

- [ ] Create `/admin/master-data/vehicle-makes` route
- [ ] Create `/admin/master-data/vehicle-makes/:id/models` route
- [ ] Implement `MakesList` component
- [ ] Implement `MakeRow` with inline editing
- [ ] Implement `ModelsList` component
- [ ] Implement `ModelRow` with inline editing
- [ ] Implement "Show Inactive" filter
- [ ] Add inactive item styling
- [ ] Connect to Vehicle MDM API endpoints
- [ ] Add RBAC-based field disabling

#### Done Criteria

- [ ] Makes and models CRUD functional
- [ ] Soft-delete policy reflected (no hard delete)
- [ ] Inactive items visually distinct
- [ ] Model navigation from make works

---

### Screen 4: Audit Log Viewer (Optional/Recommended)

**Priority:** P1 (Should Have)

#### User Stories

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| AL-01 | As Super Admin, I can view recent master data changes | List shows timestamp, user, action, resource |
| AL-02 | As Super Admin, I can filter by resource type | Dropdown: attribute, option, make, model |
| AL-03 | As Super Admin, I can see old/new values | Expandable row shows diff |

#### Technical Tasks

- [ ] Create `/admin/audit-log` route (or inline in screens)
- [ ] Implement `AuditLogList` component
- [ ] Connect to audit log API
- [ ] Implement diff viewer for changes

#### Done Criteria

- [ ] Changes traceable to user
- [ ] Old/new values visible
- [ ] Filtering functional

---

## Definition of Done (Sprint Level)

### Functional

- [ ] All P0 screens implemented
- [ ] RBAC enforced on all fields
- [ ] Error handling for 401/403/422/429/500
- [ ] Loading states on all async operations

### Quality

- [ ] No console errors
- [ ] Responsive on desktop (1280px+)
- [ ] All interactive elements have data-testid
- [ ] Manual QA pass on Chrome/Firefox

### Integration

- [ ] All API calls use correct endpoints
- [ ] Token refresh handled
- [ ] Changes reflect in Search API (integration validated)

### Documentation

- [ ] API changes documented (if any)
- [ ] Known issues logged

---

## Out of Scope (P7.3+)

| Item | Reason |
|------|--------|
| Create new attributes | Complex validation, deferred |
| Delete attributes | Soft-delete only |
| Bulk operations | MVP scope |
| Drag-drop reordering | Manual input for MVP |
| Mobile responsive | Desktop-first MVP |
| Dark mode | Not in scope |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| API endpoint changes needed | Medium | API mapping doc frozen |
| RBAC edge cases | Medium | Matrix doc covers all cases |
| Cache invalidation bugs | High | Integration scenarios defined |
| Performance on large lists | Low | Pagination implemented |

---

## Dependencies

| Dependency | Status | Owner |
|------------|--------|-------|
| Admin MDM API | ✅ Ready | Backend |
| JWT Auth | ✅ Ready | Backend |
| Audit Log API | ✅ Ready | Backend |
| Design System (Shadcn) | ✅ Ready | Frontend |

---

## Sprint Ceremonies

| Ceremony | Frequency | Notes |
|----------|-----------|-------|
| Daily Standup | Daily | Progress + blockers |
| Sprint Review | End of Sprint | Demo to stakeholders |
| Retrospective | End of Sprint | Process improvement |

---

## References

- `/app/architecture/ADMIN_UI_MIN_SCOPE_WIREFRAME_REVIEW_v1.md`
- `/app/architecture/ADMIN_UI_API_MAPPING_v1.md`
- `/app/architecture/ADMIN_UI_RBAC_BEHAVIOR_MATRIX_v1.md`
- `/app/ops/ADMIN_TO_SEARCH_INTEGRATION_SCENARIOS_v1.md`
- `/app/release_notes/PHASE_CLOSE_P7_0_STABILIZATION.md`
