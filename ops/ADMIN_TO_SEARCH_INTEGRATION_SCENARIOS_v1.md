# Admin to Search v2 Integration Scenarios

**Document ID:** ADMIN_TO_SEARCH_INTEGRATION_SCENARIOS_v1  
**Date:** 2026-02-13  
**Status:** 📋 STAGING VALIDATION REQUIRED  
**Sprint:** P7.2  

---

## Purpose

This document defines the integration scenarios between Admin Master Data changes and Search API v2 facet/filter outputs. These scenarios MUST be validated in staging before P7.2 closes.

---

## 1. Scenario: Attribute is_active = false

### Action
Super Admin sets `is_active = false` on attribute "brand"

### Expected Behavior

| Component | Before | After |
|-----------|--------|-------|
| Admin UI | Brand shown in list | Brand shown with "Inactive" badge |
| Search Facets | Brand appears in facets | Brand **removed** from facets |
| Existing Listings | Listings have brand value | Listings retain value (no data loss) |
| Filter API | `attrs={"brand":"bmw"}` works | Filter **still works** (backward compat) |

### Test Steps

```bash
# 1. Verify brand appears in facets
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.brand'

# 2. Deactivate brand attribute via Admin API
curl -X PATCH "${API}/api/v1/admin/master-data/attributes/{brand_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_active": false}'

# 3. Verify brand removed from facets
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.brand'
# Expected: null or missing

# 4. Verify existing filter still works
curl "${API}/api/v2/search?category_slug=cars&attrs={\"brand\":\"bmw\"}"
# Expected: Returns filtered results (backward compat)
```

### Acceptance Criteria

- [ ] Facet dropdown no longer shows brand
- [ ] Existing listings with brand value unaffected
- [ ] Filtering by brand still returns correct results
- [ ] No errors in logs

---

## 2. Scenario: Option is_active = false

### Action
Super Admin sets `is_active = false` on option "BMW" under brand attribute

### Expected Behavior

| Component | Before | After |
|-----------|--------|-------|
| Admin UI | BMW shown in options | BMW shown with "Inactive" badge |
| Search Facets | BMW in brand dropdown | BMW **removed** from dropdown |
| Facet Counts | BMW: 450 | BMW: 0 (or hidden) |
| Existing Listings | 450 listings have BMW | Listings retain BMW value |
| Filter API | `attrs={"brand":"bmw"}` returns 450 | Filter **still returns 450** |

### Test Steps

```bash
# 1. Get facet counts including BMW
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.brand'
# Expected: {"bmw": 450, "mercedes": 380, ...}

# 2. Deactivate BMW option
curl -X PATCH "${API}/api/v1/admin/master-data/options/{bmw_option_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_active": false}'

# 3. Verify facets updated
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.brand'
# Expected: {"mercedes": 380, ...} (BMW removed)

# 4. Verify filter still works for existing data
curl "${API}/api/v2/search?category_slug=cars&attrs={\"brand\":\"bmw\"}" | jq '.total'
# Expected: 450 (unchanged)
```

### Acceptance Criteria

- [ ] BMW no longer appears in facet dropdown
- [ ] Facet count for brand recalculated
- [ ] Direct filtering by BMW still works
- [ ] Listings data unchanged

---

## 3. Scenario: Category-Attribute Binding Change

### Action
Super Admin removes "fuel_type" binding from "motorcycles" category

### Expected Behavior

| Component | Before | After |
|-----------|--------|-------|
| Admin UI | fuel_type bound to motorcycles | Binding removed |
| Motorcycle Search Facets | fuel_type appears | fuel_type **removed** |
| Car Search Facets | fuel_type appears | fuel_type **still appears** |
| Motorcycle Listings | Have fuel_type values | Values **retained** |
| Inheritance | Child cats inherit fuel_type | Child cats **lose** facet |

### Inheritance Impact

```
vehicles (fuel_type bound)
├── cars (inherits fuel_type) ✅ Still has fuel_type
└── motorcycles (binding removed)
    └── sport-bikes (loses inherited fuel_type) ❌ No fuel_type facet
```

### Test Steps

```bash
# 1. Verify motorcycles has fuel_type facet
curl "${API}/api/v2/search?category_slug=motorcycles" | jq '.facets.fuel_type'

# 2. Remove binding (API endpoint TBD)
# Note: Binding management endpoint may need implementation

# 3. Verify motorcycles no longer has fuel_type
curl "${API}/api/v2/search?category_slug=motorcycles" | jq '.facets.fuel_type'
# Expected: null

# 4. Verify cars still has fuel_type
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.fuel_type'
# Expected: Present
```

### Acceptance Criteria

- [ ] Facet removed from target category
- [ ] Facet removed from child categories (inheritance)
- [ ] Sibling categories unaffected
- [ ] Parent category unaffected
- [ ] Existing listing data preserved

---

## 4. Scenario: Vehicle Make Deactivation

### Action
Super Admin sets `is_active = false` on make "Saab"

### Expected Behavior

| Component | Before | After |
|-----------|--------|-------|
| Admin UI | Saab in makes list | Saab with "Inactive" badge |
| New Listing Form | Saab in dropdown | Saab **removed** from dropdown |
| Search Facets | Saab in make filter | Saab **removed** from filter |
| Existing Listings | 15 listings have Saab | Listings **retained** |
| Models | 3 Saab models active | Models **also deactivated** (cascade?) |

### Cascade Decision

**Option A: Cascade Deactivate Models**
- Deactivating make auto-deactivates all its models
- Simpler UX, but may surprise admin

**Option B: Independent Deactivation**
- Make and models deactivated separately
- More control, but orphaned models possible

**DECISION:** Option B (Independent) - Admin must explicitly deactivate models

### Test Steps

```bash
# 1. Verify Saab appears in make filter
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.make'

# 2. Deactivate Saab make
curl -X PATCH "${API}/api/v1/admin/master-data/vehicle-makes/{saab_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"is_active": false}'

# 3. Verify Saab removed from facets
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.make'

# 4. Verify existing listings searchable
curl "${API}/api/v2/search?make_id={saab_id}" | jq '.total'
# Expected: 15 (unchanged)
```

### Acceptance Criteria

- [ ] Saab removed from make facet/filter
- [ ] New listings cannot select Saab
- [ ] Existing Saab listings still searchable
- [ ] Models require separate deactivation

---

## 5. Scenario: Option Label Update

### Action
Country Admin updates "BMW" label from "BMW" to "BMW (Bavarian Motor Works)"

### Expected Behavior

| Component | Before | After |
|-----------|--------|-------|
| Admin UI | "BMW" | "BMW (Bavarian Motor Works)" |
| Search Facets | "BMW" | "BMW (Bavarian Motor Works)" |
| Filter API | No change | No change (uses value, not label) |
| Listings | No change | No change |

### Test Steps

```bash
# 1. Update label
curl -X PATCH "${API}/api/v1/admin/master-data/options/{bmw_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"label": {"tr": "BMW (Bavarian Motor Works)", "de": "BMW (Bayerische Motoren Werke)"}}'

# 2. Verify facet label updated
curl "${API}/api/v2/search?category_slug=cars" | jq '.facets.brand'
# Expected: Label updated, value unchanged
```

### Acceptance Criteria

- [ ] Facet displays new label
- [ ] Filter value unchanged
- [ ] No cache issues (label updates immediately)

---

## 6. Staging Validation Checklist

| # | Scenario | Test Status | Notes |
|---|----------|-------------|-------|
| 1 | Attribute deactivation → Facet removal | ⏳ Pending | |
| 2 | Option deactivation → Facet count update | ⏳ Pending | |
| 3 | Binding removal → Inheritance effect | ⏳ Pending | May need API |
| 4 | Make deactivation → Form/facet removal | ⏳ Pending | |
| 5 | Label update → Facet label sync | ⏳ Pending | |

---

## 7. Implementation Notes

### Cache Invalidation

When Admin makes changes, Search facet cache must be invalidated:

```python
# Pseudo-code for cache invalidation
async def on_attribute_update(attr_id: str):
    await cache.delete(f"facets:*")  # Invalidate all facet caches
    
async def on_option_update(option_id: str):
    attr_id = await get_option_attribute(option_id)
    await cache.delete(f"facets:{attr_id}")
```

### Search Query Adjustments

```sql
-- Facet query must filter active options only
SELECT ao.value, ao.label, COUNT(*)
FROM listing_attributes la
JOIN attribute_options ao ON la.value_option_id = ao.id
WHERE ao.is_active = true  -- Key filter
GROUP BY ao.value, ao.label
```

---

## Gate

**P7.2 Cannot Close Until:**
1. All 5 scenarios tested in staging
2. Results documented in this file
3. Any bugs found are fixed
4. Cache invalidation verified

---

## References

- `/app/backend/app/routers/search_routes.py`
- `/app/backend/app/routers/admin_mdm_routes.py`
- `/app/architecture/SEARCH_FACET_CACHE_INVALIDATION_v1.md`
