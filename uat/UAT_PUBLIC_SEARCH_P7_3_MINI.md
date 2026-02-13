# UAT Mini Package: Public Search P7.3

**Document ID:** UAT_PUBLIC_SEARCH_P7_3_MINI  
**Date:** 2026-02-13  
**Status:** 📋 PENDING EXECUTION  
**Sprint:** P7.3  

---

## Purpose

Minimal User Acceptance Test scenarios for P7.3 Public Search Integration. All tests must pass before phase closure.

---

## Test Environment

- **Frontend URL:** `${REACT_APP_BACKEND_URL}`
- **Test User:** Anonymous (public search)
- **Data:** 270+ listings across 3 verticals

---

## Test Scenarios

### UAT-1: Category Selection → Results + Facets

**Objective:** Verify category selection loads correct results and facets

**Steps:**
1. Navigate to `/search`
2. Select "Otomobil" (cars) category
3. Observe results and sidebar

**Expected:**
- [ ] URL updates to `?category=cars`
- [ ] Results show only vehicle listings
- [ ] Facets show vehicle-related attributes (Marka, Yakıt Tipi, etc.)
- [ ] Facet counts match result count

**Priority:** P0

---

### UAT-2: Filter Apply → URL Update + Back/Forward

**Objective:** Verify filter changes update URL and browser history works

**Steps:**
1. Start at `/search?category=cars`
2. Select "BMW" from Marka facet
3. Observe URL change
4. Click browser Back button
5. Click browser Forward button

**Expected:**
- [ ] After step 2: URL = `?category=cars&attr[brand]=bmw`
- [ ] After step 4: URL = `?category=cars` (BMW filter removed)
- [ ] After step 5: URL = `?category=cars&attr[brand]=bmw` (BMW restored)
- [ ] Results update correctly at each step

**Priority:** P0

---

### UAT-3: Facet Count Consistency

**Objective:** Verify facet counts are accurate

**Steps:**
1. Navigate to `/search?category=cars`
2. Note count next to "BMW" in Marka facet
3. Select "BMW"
4. Verify total results match BMW count

**Expected:**
- [ ] BMW count (e.g., 45) matches actual results when filtered
- [ ] Other facet counts update to reflect BMW subset
- [ ] No counts show negative or impossible values

**Priority:** P0

---

### UAT-4: Deterministic Pagination

**Objective:** Verify pagination is consistent across page loads

**Steps:**
1. Navigate to `/search?category=cars&page=1`
2. Note first item title and ID
3. Navigate to page 2 (`?page=2`)
4. Navigate back to page 1
5. Refresh page

**Expected:**
- [ ] Page 1 shows same first item after back navigation
- [ ] Page 1 shows same first item after refresh
- [ ] Page 2 does not contain any items from page 1
- [ ] Total count remains consistent

**Priority:** P0

---

### UAT-5: Empty State Display

**Objective:** Verify friendly message when no results

**Steps:**
1. Navigate to `/search?category=cars`
2. Apply impossible filter combination
   - e.g., `attr[brand]=nonexistent`
3. Observe results area

**Expected:**
- [ ] "Sonuç bulunamadı" message displayed
- [ ] Suggestion to clear filters shown
- [ ] No error or blank screen
- [ ] Facet sidebar shows empty state or hidden

**Priority:** P0

---

### UAT-6: Price Range Filter

**Objective:** Verify price range filter works

**Steps:**
1. Navigate to `/search?category=cars`
2. Set price_min = 20000
3. Set price_max = 50000
4. Verify URL and results

**Expected:**
- [ ] URL = `?category=cars&price_min=20000&price_max=50000`
- [ ] All results have price between 20K-50K
- [ ] Results count updates
- [ ] Clear filter removes params

**Priority:** P1

---

### UAT-7: Sort Order Change

**Objective:** Verify sorting works correctly

**Steps:**
1. Navigate to `/search?category=cars`
2. Change sort to "Fiyat (Düşükten Yükseğe)"
3. Verify URL and result order

**Expected:**
- [ ] URL = `?category=cars&sort=price_asc`
- [ ] First result has lowest price
- [ ] Last visible result has higher price
- [ ] Default sort (date_desc) omits sort param

**Priority:** P1

---

### UAT-8: Multi-Select Facet

**Objective:** Verify multiple selections in same facet

**Steps:**
1. Navigate to `/search?category=cars`
2. Select "BMW" from Marka
3. Also select "Mercedes" from Marka
4. Verify results

**Expected:**
- [ ] URL = `?category=cars&attr[brand]=bmw,mercedes`
- [ ] Results include both BMW and Mercedes listings
- [ ] Total = BMW count + Mercedes count
- [ ] Deselecting one updates correctly

**Priority:** P1

---

### UAT-9: Mobile Filter Modal

**Objective:** Verify mobile filter UX

**Steps:**
1. Open `/search?category=cars` on mobile viewport
2. Tap "Filtrele" button
3. Select filters in modal
4. Tap "Uygula"

**Expected:**
- [ ] Filter modal opens full-screen
- [ ] All facets accessible via scroll
- [ ] "Uygula" closes modal and applies filters
- [ ] Results update after modal close

**Priority:** P1

---

### UAT-10: Deep Link Sharing

**Objective:** Verify shareable URLs work

**Steps:**
1. Apply filters: category=cars, brand=bmw, price_max=50000
2. Copy URL
3. Open URL in new incognito window

**Expected:**
- [ ] Same results displayed
- [ ] Same filters shown as selected
- [ ] No login required
- [ ] No session dependency

**Priority:** P1

---

## Test Results Template

| Test ID | Status | Notes | Tester | Date |
|---------|--------|-------|--------|------|
| UAT-1 | ⏳ | | | |
| UAT-2 | ⏳ | | | |
| UAT-3 | ⏳ | | | |
| UAT-4 | ⏳ | | | |
| UAT-5 | ⏳ | | | |
| UAT-6 | ⏳ | | | |
| UAT-7 | ⏳ | | | |
| UAT-8 | ⏳ | | | |
| UAT-9 | ⏳ | | | |
| UAT-10 | ⏳ | | | |

---

## Pass Criteria

| Priority | Required Pass Rate |
|----------|-------------------|
| P0 | 100% (5/5) |
| P1 | 80% (4/5) |

**Total:** 8/10 minimum to pass

---

## Bug Severity Classification

| Severity | Definition | Action |
|----------|------------|--------|
| Critical | Feature broken, no workaround | Block release |
| Major | Feature impaired, workaround exists | Fix before release |
| Minor | Cosmetic, edge case | Log for later |

---

## Gate Status

**P7.3 cannot close until:**
- All P0 tests pass
- 80% P1 tests pass
- No critical bugs open

---

## References

- Facet Renderer Spec: `/app/architecture/PUBLIC_SEARCH_FACET_RENDERER_SPEC_v1.md`
- URL State Spec: `/app/architecture/PUBLIC_SEARCH_URL_STATE_SPEC_v1.md`
