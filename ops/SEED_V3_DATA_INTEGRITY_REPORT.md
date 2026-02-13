# Seed v3 Data Integrity Report

**Status:** PENDING CHECK
**Target:** Seed v3 Output

## 1. Room Count Standardization
- [ ] Check `AttributeOption` table for `room_count`.
- [ ] Verify VALUES are in `["1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "6", "7+"]`.
- [ ] Ensure old values (`1+1`, `2+1`) are **DELETED** or not present.

## 2. Kitchen Attribute
- [ ] Verify `has_kitchen` attribute exists (Type: Boolean).
- [ ] Check Binding: `has_kitchen` should be linked to `housing` category (and children).
- [ ] Check Binding: `has_kitchen` must NOT be linked to `commercial`.

## 3. Localization
- [ ] Verify labels for `room_count`:
    -   Value "1": "1 Room" (EN), "1 Zimmer" (DE), "1 Oda" (TR).
-   [ ] Verify labels for `has_kitchen`:
    -   "Kitchen" (EN), "Einbauküche" (DE), "Mutfak" (TR).

## 4. Inheritance Logic
-   [ ] `m2_gross` linked to Root `real_estate` -> Inherited by `apartment-sale`.
-   [ ] `ceiling_height` linked to `commercial` -> Inherited by `warehouse`.
