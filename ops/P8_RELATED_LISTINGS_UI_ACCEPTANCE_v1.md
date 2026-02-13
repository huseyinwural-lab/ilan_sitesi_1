# P8 Related Listings UI Acceptance

**Document ID:** P8_RELATED_LISTINGS_UI_ACCEPTANCE_v1  
**Date:** 2026-02-13  
**Status:** 📝 PENDING VALIDATION  

---

## 1. UI Requirements
- **Location:** Bottom of the Detail Page.
- **Layout:** Grid (1 col mobile, 2 col tablet, 4 col desktop).
- **Content:** Card showing Image, Title, Price, Currency.
- **Interaction:** Click navigates to that listing's detail page.

## 2. Data Logic
- **Source:** `/api/v2/listings/{id}` -> `related` field.
- **Criteria:** Same Category, Active Status, Exclude current listing.
- **Limit:** Max 4 items.

## 3. Test Scenarios

### 3.1. Rendering
- **Scenario:** Open a listing with other active listings in the same category.
- **Expected:** "Benzer İlanlar" section is visible with 1-4 cards.

### 3.2. Navigation
- **Scenario:** Click a related listing card.
- **Expected:** URL changes to new listing, page scrolls to top, content updates.

### 3.3. Empty State
- **Scenario:** Open a listing in a category with no other items.
- **Expected:** "Benzer İlanlar" section is hidden (not rendered).

---

## 4. Verification
*(To be filled after manual/auto test)*
- [ ] Render verified
- [ ] Navigation verified
- [ ] Empty state verified
