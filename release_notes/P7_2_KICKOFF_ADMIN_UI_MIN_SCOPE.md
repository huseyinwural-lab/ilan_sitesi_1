# P7.2 Kickoff: Admin UI Minimum Scope

**Document ID:** P7_2_KICKOFF_ADMIN_UI_MIN_SCOPE  
**Date:** 2026-02-13  
**Status:** 🚀 ACTIVE  
**Sprint:** P7.2  

---

## Sprint Officially Started

P7.2 Admin UI Minimum Scope sprint has been officially kicked off following the successful completion of all prerequisite gates.

---

## Prerequisites Verified

| Gate | Document | Status |
|------|----------|--------|
| P7.0 Closure | `/app/release_notes/PHASE_CLOSE_P7_0_STABILIZATION.md` | ✅ |
| Wireframe Freeze | `/app/architecture/ADMIN_UI_MIN_SCOPE_WIREFRAME_REVIEW_v1.md` | ✅ |
| API Mapping | `/app/architecture/ADMIN_UI_API_MAPPING_v1.md` | ✅ |
| RBAC Matrix | `/app/architecture/ADMIN_UI_RBAC_BEHAVIOR_MATRIX_v1.md` | ✅ |
| Integration Scenarios | `/app/ops/ADMIN_TO_SEARCH_INTEGRATION_SCENARIOS_v1.md` | ✅ |
| Sprint Backlog | `/app/tasks/P7_2_ADMIN_UI_SPRINT_BACKLOG_v1.md` | ✅ |

---

## Scope

### In Scope (Must Deliver)

| Screen | Description | Priority |
|--------|-------------|----------|
| Screen 1 | Attributes Management (List, Filter, Inline Edit, RBAC) | P0 |
| Screen 2 | Options Management (Parent Context, Breadcrumb, RBAC) | P0 |
| Screen 3 | Vehicle Makes/Models (Soft-Delete, Inactive Styling, RBAC) | P0 |

### Out of Scope

- Create new attributes/options (complex validation)
- Bulk operations
- Drag-drop reordering (manual input only)
- Mobile responsive
- Dark mode
- Audit log viewer (optional, P1)

---

## Definition of Done

### Per-Screen Criteria

| Criterion | Required |
|-----------|----------|
| List view with pagination | ✅ |
| Search/filter functionality | ✅ |
| Inline editing for allowed fields | ✅ |
| RBAC field restrictions (disable/hide) | ✅ |
| Error handling (401/403/422/429) | ✅ |
| Toast notifications | ✅ |
| Loading states | ✅ |
| data-testid on all interactive elements | ✅ |

### Sprint-Level Criteria

| Criterion | Required |
|-----------|----------|
| All 3 screens implemented | ✅ |
| RBAC enforced on UI + Backend | ✅ |
| UI-to-API smoke test passed | ✅ |
| Admin→Search integration scenarios validated | ✅ |
| No console errors | ✅ |
| Manual QA passed | ✅ |

---

## Execution Order

```
Screen 1: Attributes
    ↓ Acceptance doc
Screen 2: Options  
    ↓ Acceptance doc
Screen 3: Vehicle MDM
    ↓ Acceptance doc
    ↓
UI-to-API Smoke Test
    ↓
Admin→Search Staging Validation (GATE)
    ↓
P7.2 Closure
```

---

## Closing Gates

### Gate 1: UI-to-API Smoke (Per Screen)

Each screen must pass:
- Country Admin label update → 200 + audit log
- Unauthorized field change attempt → 403
- Invalid payload → 422 + field errors

### Gate 2: Admin→Search Integration (Sprint Closure)

**BLOCKING GATE** - P7.2 cannot close without:

| Scenario | Validation |
|----------|------------|
| Option is_active=false | Facet count updates |
| Attribute is_filterable=false | Facet removed |
| Binding change | Inheritance effect verified |

Reference: `/app/ops/ADMIN_TO_SEARCH_INTEGRATION_SCENARIOS_v1.md`

---

## Team Assignments

| Role | Responsibility |
|------|----------------|
| Agent | Implementation |
| User | Review & Approval |

---

## Risk Monitoring

| Risk | Mitigation | Status |
|------|------------|--------|
| API contract deviation | Frozen API mapping doc | 🟢 |
| RBAC edge cases | Comprehensive matrix | 🟢 |
| Integration bugs | Staging validation gate | 🟢 |

---

## Communication

- Progress updates after each screen completion
- Blockers escalated immediately
- Acceptance docs for sign-off

---

**Sprint Start Date:** 2026-02-13  
**Target:** 3 screens + validation gates

---

## References

- `/app/tasks/P7_2_ADMIN_UI_SPRINT_BACKLOG_v1.md`
- `/app/architecture/ADMIN_UI_MIN_SCOPE_WIREFRAME_REVIEW_v1.md`
- `/app/architecture/ADMIN_UI_API_MAPPING_v1.md`
