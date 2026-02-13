# P7.2 Admin UI Visual QA Notes

**Document ID:** P7_2_ADMIN_UI_VISUAL_QA_NOTES  
**Date:** 2026-02-13  
**Status:** 📋 OPTIONAL - Does not block P7.3  
**Sprint:** P7.2 (Post-Close QA)  

---

## Purpose

Document visual quality observations for Admin UI screens. This is a non-blocking quality improvement exercise.

---

## Screen 1: Admin Attributes

### RBAC UI Appearance

| Element | Super Admin | Country Admin | Notes |
|---------|-------------|---------------|-------|
| is_active toggle | ✅ Visible, clickable | ✅ Visible, disabled | Gray opacity applied |
| is_filterable toggle | ✅ Visible, clickable | ✅ Visible, disabled | Gray opacity applied |
| display_order input | ✅ Editable | ❌ Read-only text | Shows value, no input |
| Options link | ✅ Visible | ✅ Visible | Same for both roles |

### Inactive Styling

| State | Visual Treatment |
|-------|------------------|
| Active row | Normal opacity (1.0) |
| Inactive row | Reduced opacity (0.5) + muted background |

**Observation:** ⏳ Pending visual verification

### Inline Edit UX

| Behavior | Status | Notes |
|----------|--------|-------|
| Click to edit | ⏳ | Opens input inline |
| Enter to save | ⏳ | Saves and closes |
| Escape to cancel | ⏳ | Reverts value |
| Error message | ⏳ | Toast notification |

---

## Screen 2: Admin Options

### Breadcrumb Navigation

| Element | Expected | Actual |
|---------|----------|--------|
| Back arrow | ← Attributes | ⏳ |
| Parent name | {Attribute Name} | ⏳ |
| Current | Options | ⏳ |

### Empty State

| Scenario | Expected Message |
|----------|------------------|
| No options | "Seçenek bulunamadı" |
| Loading | Spinner |

---

## Screen 3: Vehicle MDM

### Inactive Item Styling

| Element | Active | Inactive |
|---------|--------|----------|
| Row background | Normal | bg-muted/20 |
| Text color | Normal | Muted |
| Toggle icon | Green | Gray |

### Show Inactive Filter

| State | Checkbox | List Content |
|-------|----------|--------------|
| Unchecked (default) | ☐ | Active items only |
| Checked | ☑ | All items |

---

## Mobile Responsiveness

### Breakpoints

| Viewport | Sidebar | Content |
|----------|---------|---------|
| Desktop (>1024px) | Fixed 280px | Full table |
| Tablet (768-1024px) | Collapsible | Responsive table |
| Mobile (<768px) | Hidden, hamburger | Scrollable |

**Note:** Admin UI is desktop-first; mobile polish is P8+

---

## Accessibility Notes

| Item | Status | Notes |
|------|--------|-------|
| Focus indicators | ⏳ | Tab navigation |
| ARIA labels | ⏳ | Screen reader support |
| Color contrast | ⏳ | Inactive state readability |
| Keyboard nav | ⏳ | Enter/Escape shortcuts |

---

## Improvement Suggestions

| Priority | Suggestion | Effort |
|----------|------------|--------|
| Low | Add tooltip on disabled toggles | 1h |
| Low | Animate row on save success | 2h |
| Medium | Add bulk selection checkboxes | 4h |
| Medium | Drag-drop for sort order | 8h |

---

## Gate Status

**This document is OPTIONAL and does NOT block P7.3.**

Visual QA can be performed in parallel with P7.3 development.

---

## Next Steps

1. When preview is available, capture screenshots
2. Document any visual bugs found
3. Create tickets for P8 polish sprint

---

## References

- Admin Attributes: `/app/frontend/src/pages/AdminAttributes.js`
- Admin Options: `/app/frontend/src/pages/AdminOptions.js`
- Admin Vehicle MDM: `/app/frontend/src/pages/AdminVehicleMDM.js`
